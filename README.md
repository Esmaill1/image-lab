
# IMAGE-LAB
[ main branch ](https://github.com/Esmaill1/image-lab/tree/main)
##  Infrastructure & DevOps

This project is deployed using a production-grade CI/CD pipeline, ensuring consistent environments and zero-manual-effort updates.

**Architecture Overview:**
* **Containerization:** Application is fully Dockerized (custom `Dockerfile`) to isolate dependencies and ensure reproducibility across development and production.
* **CI/CD Pipeline:** A GitHub Actions workflow automatically triggers on commits to `main`. It handles:
    * SSH authentication to the AWS EC2 instance.
    * Pulling the latest code and rebuilding Docker images.
    * Seamless container replacement.
* **Networking & Security:**
    * **Reverse Proxy:** Nginx is configured as a reverse proxy to handle client requests, manage timeouts for long-processing tasks, and enforce file upload limits.
    * **SSL/TLS:** Automated HTTPS encryption via Let's Encrypt (Certbot).
    * **DNS:** Custom domain mapping (`imageprocessing.esmail.app`) via A Records.
