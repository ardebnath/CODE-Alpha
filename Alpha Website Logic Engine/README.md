# Alpha Website Logic Engine

This folder contains a standalone product that uses Alpha as the readable scripting layer behind websites, forms, and admin tools.

What it includes:

- a browser dashboard for editing Alpha website logic
- website form data and admin data JSON testers
- reusable saved Alpha scripts
- built-in logic templates
- a public API route for external forms or websites
- local execution logs

Run it with:

```powershell
python "Alpha Website Logic Engine/engine_server.py"
```

Open:

```text
http://127.0.0.1:8095
```

For phones or other PCs on the same trusted Wi-Fi:

```powershell
python "Alpha Website Logic Engine/engine_server.py" --share-lan
```

Public API route:

```text
POST /api/public/execute
```

Payload example:

```json
{
  "script_key": "contact_form",
  "form_data": {
    "name": "Aritra",
    "email": "aritra@example.com",
    "message": "Hello from a website"
  },
  "admin_data": {
    "role": "manager",
    "action": "approve_order"
  }
}
```
