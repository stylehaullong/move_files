function moveRIAFile ($hostName, $keyFilePath, $filePath, $sftpPath) {
    # Define UserName
    $UserName = "e01692"
    $nopasswd = new-object System.Security.SecureString

    #Set Credetials to connect to server
    $Credential = New-Object System.Management.Automation.PSCredential ($UserName, $nopasswd)

    # Set local file path, SFTP path, and the backup location path which I assume is an SMB path
    $allFilesMatchingPattern = @()

    $FolderPath = (Get-Item $filePath).Directory
    Get-ChildItem $FolderPath | 
    ForEach-Object { 
        if($_.BaseName -Match 'NR_NEXT*') {
            $allFilesMatchingPattern += $_.FullName
        }
    }

    # Establish the SFTP connection
    $SFTPSession = New-SFTPSession -ComputerName $hostName -Credential $Credential -KeyFile $keyFilePath
    # Upload the file to the SFTP path
    foreach($file in $allFilesMatchingPattern) {
        Set-SFTPFile -SessionId $SFTPSession.SessionID -LocalFile $file -RemotePath $SftpPath
    }
    # Disconnect SFTP session
    $SFTPSession.Disconnect()
}




