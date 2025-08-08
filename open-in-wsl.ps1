# SpineLift Rails - Open in WSL
Write-Host "Opening SpineLift Rails in WSL..." -ForegroundColor Green

# Cursor를 사용하는 경우
if (Get-Command cursor -ErrorAction SilentlyContinue) {
    cursor --remote wsl+Ubuntu /home/hoons/spineLiftRails
}
# VS Code를 사용하는 경우
elseif (Get-Command code -ErrorAction SilentlyContinue) {
    code --remote wsl+Ubuntu /home/hoons/spineLiftRails
}
else {
    Write-Host "Neither Cursor nor VS Code found in PATH!" -ForegroundColor Red
}