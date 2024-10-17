$pythonExe = "C:\Users\PC-TESTER\Desktop\proyectos\Drones\Drones\Scripts\python.exe"
$scriptPath = "C:\Users\PC-TESTER\Desktop\proyectos\Drones\AD_Drone.py"

1..15 | ForEach-Object {
    # Convertir el n�mero a string.
    $iAsString = "$_"
    # Determinar si se usa "si" o "no" y tambi�n tratarlo como string.
    $siNo = if ($_ -eq 1) { "si" } else { "no" }
    # Construir los argumentos como strings.
    $argumentos = "$iAsString $iAsString $siNo"
    Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "& {& `"$pythonExe`" `"$scriptPath`" $argumentos}"
    # Pausa de 3 segundos antes de continuar con la siguiente iteraci�n.
    
    if ($_ -eq 1) { Start-Sleep -Seconds 5 } else { Start-Sleep -Seconds 2 }
     
}
