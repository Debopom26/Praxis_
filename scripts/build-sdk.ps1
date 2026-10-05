param([string]$JavaHome = $env:JAVA_HOME)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $JavaHome) { throw 'Set JAVA_HOME or pass -JavaHome with a compatible JDK 17-23 installation.' }
$env:JAVA_HOME = $JavaHome
$env:GRADLE_USER_HOME = Join-Path $projectRoot '.cache\gradle'
$env:ANDROID_HOME = Join-Path $projectRoot '.tools\android-sdk'
$env:ANDROID_USER_HOME = Join-Path $projectRoot '.cache\android-user'
$jvmUserPath = Join-Path $projectRoot '.cache\jvm-user'
$null = New-Item -ItemType Directory -Force -Path $env:ANDROID_USER_HOME, $jvmUserPath
$gradlePath = Join-Path $projectRoot '.tools\gradle-8.11.1\bin\gradle.bat'
if (-not (Test-Path -LiteralPath $gradlePath)) { throw 'Run scripts/bootstrap_android.py first.' }
& $gradlePath "-Duser.home=$jvmUserPath" -p (Join-Path $projectRoot 'android-sdk') --no-daemon :praxis:testDebugUnitTest :praxis:lintRelease :praxis:assembleRelease
if ($LASTEXITCODE -ne 0) { throw 'SDK build or verification failed.' }
