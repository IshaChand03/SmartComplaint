$root = (Get-Location).Path
$utf8 = New-Object System.Text.UTF8Encoding($false)

New-Item -ItemType Directory -Force -Path "$root\docs\css", "$root\docs\js" | Out-Null
Copy-Item "$root\static\css\style.css" "$root\docs\css\style.css" -Force
Copy-Item "$root\static\js\common.js" "$root\docs\js\common.js" -Force

$scripts = '<script src="js/common.js"></script>' + "`r`n  " + '<script src="js/mock-api.js"></script>'
$pages = "login", "register", "dashboard", "complaints", "complaint-new", "complaint-details", "queues", "admin"

foreach ($name in $pages) {
    $text = [System.IO.File]::ReadAllText("$root\templates\$name.html", $utf8)
    $text = $text.Replace('/static/css/style.css', 'css/style.css')
    $text = $text.Replace('<script src="/static/js/common.js"></script>', $scripts)
    $text = $text.Replace('<a href="/register">', '<a href="register.html">')
    $text = $text.Replace('<a href="/login">', '<a href="login.html">')
    $text = $text.Replace('window.location.href = "/dashboard";', 'window.location.href = "dashboard.html";')
    $text = $text.Replace('window.location.href = "/login";', 'window.location.href = "login.html";')
    $text = $text.Replace('link.href = "/complaints/" + c.id;', 'link.href = "complaint-details.html?id=" + c.id;')
    $text = $text.Replace('window.location.href = "/complaints/" + result.data.id;', 'window.location.href = "complaint-details.html?id=" + result.data.id;')
    $text = $text.Replace('window.location.pathname.split("/").pop()', 'new URLSearchParams(window.location.search).get("id")')
    [System.IO.File]::WriteAllText("$root\docs\$name.html", $text, $utf8)
}

[System.IO.File]::WriteAllText("$root\docs\index.html", '<meta http-equiv="refresh" content="0; url=login.html">', $utf8)
Write-Host "Demo pages created in the docs folder."