# Enable TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Function to create directory if it doesn't exist
function Create-DirectoryIfNotExists {
    param([string]$Path)
    if (-not (Test-Path -Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

# Function to sanitize filename
function Get-SanitizedFilename {
    param([string]$Filename)
    $invalidChars = [IO.Path]::GetInvalidFileNameChars()
    return ($Filename.Split($invalidChars) -join '')
}

# Function to download file
function Download-File {
    param(
        [string]$Url,
        [string]$FilePath,
        [int]$MaxRetries = 3
    )
    
    # Disable progress bar for faster downloads
    $ProgressPreference = 'SilentlyContinue'
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Write-Host "Download attempt $i of $MaxRetries..." -ForegroundColor Gray
            
            $headers = @{
                "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Download the file using Invoke-WebRequest
            $response = Invoke-WebRequest -Uri $Url -Headers $headers -UseBasicParsing -OutFile $FilePath
            
            # If we get here, download was successful
            return $true
        }
        catch {
            Write-Host "Attempt $i failed: $($_.Exception.Message)" -ForegroundColor Yellow
            
            if ($i -eq $MaxRetries) {
                Write-Host "Error downloading $Url after $MaxRetries attempts: $_" -ForegroundColor Red
                return $false
            }
            
            # Wait before retrying (exponential backoff)
            $waitSeconds = [Math]::Pow(2, $i)
            Write-Host "Waiting $waitSeconds seconds before retry..." -ForegroundColor Yellow
            Start-Sleep -Seconds $waitSeconds
        }
    }
    return $false
}

# Function to get album URLs
function Get-AlbumUrls {
    $baseUrl = 'https://zeldauniverse.net/media/music/'
    try {
        $headers = @{
            "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        Write-Host "Sending request to $baseUrl..."
        $response = Invoke-WebRequest -Uri $baseUrl -Headers $headers -UseBasicParsing
        Write-Host "Response received. Processing links..."
        
        $albumLinks = @()
        
        $response.Links | ForEach-Object {
            $href = $_.href
            if ($href -like '*/media/music/*' -and $href -ne $baseUrl) {
                Write-Host "Found album link: $href" -ForegroundColor Gray
                $albumLinks += $href
            }
        }
        
        if ($albumLinks.Count -eq 0) {
            Write-Host "No album links found. Response content:" -ForegroundColor Yellow
            Write-Host $response.Content
        }
        
        return $albumLinks
    }
    catch {
        Write-Host "Error getting album URLs: $_" -ForegroundColor Red
        Write-Host "Exception details: $($_.Exception.Message)" -ForegroundColor Red
        return @()
    }
}

# Function to process album page
function Get-MP3Links {
    param([string]$AlbumUrl)
    try {
        $headers = @{
            "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        $response = Invoke-WebRequest -Uri $AlbumUrl -Headers $headers -UseBasicParsing
        $mp3Links = @()
        
        $response.Links | ForEach-Object {
            $href = $_.href
            if ($href -like '*.mp3' -and $href -like '*zeldauniverse.s3.amazonaws.com*') {
                $filename = [System.Web.HttpUtility]::UrlDecode(($href -split '/')[-1])
                $mp3Links += @{
                    Url = $href
                    Filename = $filename
                }
            }
        }
        return $mp3Links
    }
    catch {
        Write-Host "Error processing album page: $_" -ForegroundColor Red
        return @()
    }
}

# Main script
Add-Type -AssemblyName System.Web

# Create base directory
$baseDir = "zelda_music"
Create-DirectoryIfNotExists -Path $baseDir

# Get all album URLs
Write-Host "Getting album list..." -ForegroundColor Cyan
$albumUrls = Get-AlbumUrls
Write-Host "Found $($albumUrls.Count) albums"

if ($albumUrls.Count -eq 0) {
    Write-Host "No albums found. Exiting..." -ForegroundColor Red
    exit 1
}

# Process each album
foreach ($albumUrl in $albumUrls) {
    # Get album name from URL
    $albumName = $albumUrl.TrimEnd('/').Split('/')[-1].Replace('-', ' ')
    $albumName = (Get-Culture).TextInfo.ToTitleCase($albumName)
    Write-Host "`nProcessing album: $albumName" -ForegroundColor Cyan
    
    # Create album directory
    $albumDir = Join-Path $baseDir (Get-SanitizedFilename -Filename $albumName)
    Create-DirectoryIfNotExists -Path $albumDir
    
    # Get MP3 links from album page
    $mp3Links = Get-MP3Links -AlbumUrl $albumUrl
    Write-Host "Found $($mp3Links.Count) tracks"
    
    # Download each MP3
    foreach ($mp3 in $mp3Links) {
        $filepath = Join-Path $albumDir (Get-SanitizedFilename -Filename $mp3.Filename)
        
        if (-not (Test-Path $filepath)) {
            Write-Host "Downloading: $($mp3.Filename)"
            if (Download-File -Url $mp3.Url -FilePath $filepath) {
                Write-Host "Successfully downloaded: $($mp3.Filename)" -ForegroundColor Green
            }
            else {
                Write-Host "Failed to download: $($mp3.Filename)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "Skipping existing file: $($mp3.Filename)" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nDownload complete!" -ForegroundColor Green 