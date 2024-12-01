bind = "0.0.0.0:8000"  # Listen on all network interfaces
workers = 3  # Number of worker processes
timeout = 120  # Timeout in seconds
accesslog = "access.log"
errorlog = "error.log"
capture_output = True
enable_stdio_inheritance = True
