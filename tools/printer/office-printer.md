# Office Printer

## Device Info

- **Name:** Office Printer
- **Address:** `ipp://<PRINTER_IP>:631/ipp/print`
- **Toner:** Check via `lpstat -p office-printer`
- **Integration:** CUPS (system-level, not HA)
- **CUPS Queue Name:** `office-printer`

## Setup (one-time)

CUPS must be installed and the printer added before printing works.

```bash
sudo apt-get install -y cups
sudo lpadmin -p office-printer -E -v ipp://<PRINTER_IP>:631/ipp/print -m everywhere
sudo lpoptions -d office-printer
```

If CUPS isn't running: `sudo systemctl start cups`

## Commands

### Print a file
```bash
lp -d office-printer /tmp/<filename>
```

### When user uploads a file to Discord
1. Save the uploaded file to `/tmp/`
2. Run: `lp -d office-printer /tmp/<filename>`
3. Confirm the print job was sent

### Check printer status
```bash
lpstat -p office-printer
```

### Check print queue
```bash
lpq -P office-printer
```

### Cancel a print job
```bash
cancel -a office-printer
```

## Quirks

- None known yet.
