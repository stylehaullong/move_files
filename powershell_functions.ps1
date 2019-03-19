$filePath = 'C:\Users\L.Nguyen\Documents\Development\RIA\NR_NEXT_AUDIT.CYD.20190312.231216.txt'
$FolderPath = (Get-Item $filePath).Directory
$fileNameAndPath = @()
Get-ChildItem $FolderPath | 
ForEach-Object { 
    if($_.BaseName -Match 'NR_NEXT*') {
        $fileNameAndPath += $_.FullName
    }
}

foreach($file in $fileNameAndPath) {
    echo $file
}