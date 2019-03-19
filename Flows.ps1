Param(
    [String]$ConfigFile = "E:\Flows\Configs.json",
    [String]$ThisJobName
)
  

$Configs = Get-Content $ConfigFile | ConvertFrom-Json
$Jobs = $Configs.Jobs
$Queues = $Configs.Queues

$ThisJobIndex = -1

ForEach ($ThisJob in $Jobs){ 
    if($ThisJob.JobName -eq $ThisJobName){
        $ThisJobIndex = $Jobs.indexof($ThisJob)
        break
    }
}

ForEach ($ThisJobQueue in $Jobs[$ThisJobIndex].JobQueues){
    $QueueSize = 0 
    ForEach ($Queue in $Queues){
        if($Queue.QueueName -eq $ThisJobQueue){
            $QueueFile = $Queue.QueueFile
            $QueueLoc = $Queue.QueueLoc
            $QueuePath = $QueueLoc + $QueueFile
            ForEach ($QueueJobs in $Jobs){
                if ($QueueJobs.JobQueues -eq $Queue.QueueName){
                    $QueueSize++
                }
            }
            if(Test-Path $QueuePath){
                Add-Content -path $QueuePath -value $ThisJobName
            }
            else {
                New-Item -path $QueuePath -type file -value "$ThisJobName`r`n"
            }
            if((Get-Content -path $QueuePath | select -first 1 -skip ($QueueSize-1)) -eq $ThisJobName){
                ForEach ($NextJob in $Queue.NextJobs){
                    $Script = '"C:\Program Files\Informatica Cloud Secure Agent\apps\runAJobCli\cli.bat" runAJobCli -n ' + $NextJob.NextJobName + ' -t ' + $NextJob.NextJobType + ' -w false' 
                    cmd.exe /c $Script
                    Remove-Item -path $QueuePath
                }
            }
        }
    }
}