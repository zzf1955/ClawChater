Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

' 切换到项目目录并启动
WshShell.CurrentDirectory = strPath
WshShell.Run "cmd /c conda activate recall && pythonw main.py", 0, False
