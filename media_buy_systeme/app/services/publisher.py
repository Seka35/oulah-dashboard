"""
Publisher Service — Upload landing pages to VPS

Uses rsync over SSH to publish landing pages to:
- VPS: 178.105.100.232
- Path: /opt/launch-engine/landings/<slug>/
- URL: https://ignuva.shop/<slug>
"""
import os
import re
import subprocess
import shutil
from pathlib import Path

VPS_HOST = os.getenv("VPS_HOST", "178.105.100.232")
VPS_USER = os.getenv("VPS_USER", "root")
VPS_SSH_KEY = os.getenv("VPS_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))
VPS_LANDINGS_DIR = os.getenv("VPS_LANDINGS_DIR", "/opt/launch-engine/landings")
LANDINGS_BASE_URL = os.getenv("LANDINGS_BASE_URL", "https://ignuva.shop")


def slugify(name: str) -> str:
    """Convert product name to URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def publish_to_vps(slug: str, html_content: str, assets_local_path: str = None) -> dict:
    """
    Publish a landing page to the VPS via rsync over SSH.

    Args:
        slug: URL-safe product slug (e.g., "nike-air-force-blue")
        html_content: Full HTML of the landing page
        assets_local_path: Optional local path to assets folder to upload

    Returns:
        {"success": bool, "url": str, "error": str}
    """
    import tempfile

    # Create temp directory for this landing
    temp_dir = Path(tempfile.mkdtemp(prefix="landing_"))
    slug_dir = temp_dir / slug
    slug_dir.mkdir(exist_ok=True)

    try:
        # Write HTML file
        index_path = slug_dir / "index.html"
        index_path.write_text(html_content, encoding="utf-8")

        # Copy assets if provided
        if assets_local_path and os.path.exists(assets_local_path):
            assets_dest = slug_dir / "assets"
            if assets_dest.exists():
                shutil.rmtree(assets_dest)
            shutil.copytree(assets_local_path, assets_dest)

        # Build rsync command
        ssh_cmd = f"ssh -i {VPS_SSH_KEY} -o StrictHostKeyChecking=no"
        rsync_cmd = [
            "rsync", "-avz",
            "-e", ssh_cmd,
            str(slug_dir) + "/",
            f"{VPS_USER}@{VPS_HOST}:{VPS_LANDINGS_DIR}/{slug}/"
        ]

        result = subprocess.run(
            rsync_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {
                "success": False,
                "url": "",
                "error": result.stderr
            }

        public_url = f"{LANDINGS_BASE_URL}/{slug}"
        return {
            "success": True,
            "url": public_url,
            "slug": slug,
            "vps_path": f"{VPS_LANDINGS_DIR}/{slug}"
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "url": "",
            "error": "rsync timeout (60s)"
        }
    except Exception as e:
        return {
            "success": False,
            "url": "",
            "error": str(e)
        }
    finally:
        # Cleanup temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)


def unpublish_from_vps(slug: str) -> dict:
    """
    Delete a landing page from the VPS.

    Returns:
        {"success": bool, "error": str}
    """
    ssh_cmd = f"ssh -i {VPS_SSH_KEY} -o StrictHostKeyChecking=no"
    rm_cmd = f"rm -rf {VPS_LANDINGS_DIR}/{slug}"

    result = subprocess.run(
        ["ssh", "-i", VPS_SSH_KEY, "-o", "StrictHostKeyChecking=no",
         f"{VPS_USER}@{VPS_HOST}", rm_cmd],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        return {"success": False, "error": result.stderr}

    return {"success": True, "slug": slug}


def list_vps_landings() -> dict:
    """
    List all landing pages currently on the VPS.

    Returns:
        {"success": bool, "landings": list[dict], "error": str}
    """
    ssh_cmd = f"ssh -i {VPS_SSH_KEY} -o StrictHostKeyChecking=no"
    list_cmd = f"ls -1 {VPS_LANDINGS_DIR}/ 2>/dev/null | grep -v '^$'"

    result = subprocess.run(
        ["ssh", "-i", VPS_SSH_KEY, "-o", "StrictHostKeyChecking=no",
         f"{VPS_USER}@{VPS_HOST}", list_cmd],
        capture_output=True,
        text=True,
        timeout=15
    )

    if result.returncode != 0:
        return {"success": False, "landings": [], "error": result.stderr}

    slugs = [s.strip() for s in result.stdout.split("\n") if s.strip()]
    landings = [{"slug": s, "url": f"{LANDINGS_BASE_URL}/{s}"} for s in slugs]

    return {"success": True, "landings": landings}


def test_vps_connection() -> dict:
    """
    Test SSH connection to VPS.

    Returns:
        {"success": bool, "message": str}
    """
    result = subprocess.run(
        ["ssh", "-i", VPS_SSH_KEY, "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         f"{VPS_USER}@{VPS_HOST}", "echo ok"],
        capture_output=True,
        text=True,
        timeout=15
    )

    if result.returncode == 0 and "ok" in result.stdout:
        return {"success": True, "message": f"Connected to {VPS_HOST}"}
    else:
        return {"success": False, "message": result.stderr or "Connection failed"}