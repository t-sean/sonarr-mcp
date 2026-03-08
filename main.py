import logging
import os
from dotenv import load_dotenv
load_dotenv()

SONARR_API_KEY = os.getenv("SONARR_API_KEY")
MCP_PORT = int(os.getenv("MCP_PORT", "8787"))
MCP_HOST = os.getenv("MCP_HOST", "localhost")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if not SONARR_API_KEY:
    logging.error("SONARR_API_KEY environment variable is not set.")
    exit(1)

# Import mcp instance with registered tools
from tools import mcp

if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_HOST, port=MCP_PORT)
