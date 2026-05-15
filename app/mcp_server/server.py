from mcp.server.fastmcp import (
    FastMCP,
)

from app.logger import get_logger
from app.mcp_server.tools import (
    register_tools,
)

logger = get_logger("mcp_server")

mcp = FastMCP(
    "mcp-trading-bot"
)

register_tools(mcp)

logger.info(
    "mcp_server_initialized"
)

if __name__ == "__main__":

    logger.info(
        "starting_mcp_server"
    )

    mcp.run()
