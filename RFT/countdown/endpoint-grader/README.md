# Optional Countdown Endpoint Grader

This Azure Function exposes the Countdown arithmetic grader over HTTP. It was
originally contributed by Dave Voutila and is retained as an optional example
for environments that support endpoint graders.

The primary notebook uses an inline Python grader. Prefer that path unless a
hosted endpoint is specifically required.

```powershell
az deployment group create `
  --resource-group <resource-group> `
  --template-file main.bicep `
  --parameters functionAppName=<unique-name>
```

Deploy the Python function package separately, keep function-level
authentication enabled, and store its key outside source control.
