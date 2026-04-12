# Welcome to your organization's demo respository
This code repository (or "repo") is designed to demonstrate the best GitHub has to offer with the least amount of noise.

The repo includes an `index.html` file (so it can render a web page), two GitHub Actions workflows, and a CSS stylesheet dependency.

For local PPST demo data, run `python manage.py generate_fake_data 10`.
Replace `10` with however many fake patient test sessions you want to generate. Each run creates a random mix of completed and pending sessions.
You can also target a specific clinician with `python manage.py generate_fake_data 10 --clinician abc@abc.com`.
To remove sessions for a clinician, run `python manage.py clear_fake_data --clinician abc@abc.com --yes`.
