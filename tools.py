import logging
import requests
import os
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("sonarr-mcp")

SONARR_URL = os.getenv("SONARR_URL", "http://localhost:7878")
SONARR_API_KEY = os.getenv("SONARR_API_KEY")

def _make_api_request(endpoint: str, method: str = "GET", **kwargs) -> dict:
    """Make API request with consistent error handling."""
    try:
        response = requests.request(
            method,
            f"{SONARR_URL}/api/v3/{endpoint}",
            headers={"X-Api-Key": SONARR_API_KEY},
            **kwargs
        )
        response.raise_for_status()
        
        # Handle empty responses (e.g., DELETE returning 200/204)
        if response.status_code == 204 or not response.content:
            return {"success": True}
        
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}

@mcp.tool()  
def get_download_queue() -> list[dict]:
    """Get the current download queue from Sonarr. Use this to find broken or stalled downloads."""
    logging.info("Fetching download queue...")
    queue = _make_api_request("queue")
    records = queue.get("records", []) if isinstance(queue, dict) else []
    logging.info(f"Found {len(records)} item(s) in the download queue.")
    return [
        {
            "queueId": r.get("id"),
            "seriesId": r.get("seriesId"),
            "seasonNumber": r.get("seasonNumber"),
            "episodeId": r.get("episodeId"),
            "title": r.get("title"),
            "status": r.get("status"),
            "trackedDownloadStatus": r.get("trackedDownloadStatus"),
            "statusMessages": r.get("statusMessages"),
            "errorMessage": r.get("errorMessage"),
        }
        for r in records
    ]

@mcp.tool()
def clear_download_queue_item(queue_id: int) -> dict:
    """Remove an item from the download queue by its queue ID."""
    logging.info(f"Clearing download queue item with ID: {queue_id}...")
    result = _make_api_request(f"queue/{queue_id}", method="DELETE")
    if "success" in result:
        logging.info(f"Successfully cleared queue item with ID: {queue_id}.")
        return {"success": True}
    else:
        logging.error(f"Failed to clear queue item with ID: {queue_id}.")
        return {"error": "Failed to clear queue item."}

@mcp.tool() 
def download_episodes(episode_ids: list[int]):
    """Trigger download for specific episodes by their episode IDs."""
    logging.info(f"Triggering download for episode IDs: {episode_ids}...")
    result = _make_api_request(f"command", method="POST", json={
        "name": "EpisodeSearch",
        "episodeIds": episode_ids
    })
    return result.get("status")

@mcp.tool()
def download_series(series_id: int, season_number: int | None):
    """Trigger download for all missing episodes in a series by its series ID. And optionally a specific season number."""
    logging.info(f"Triggering download for series ID: {series_id}...")
    params = {
        "name": "SeriesSearch",
        "seriesId": series_id
    }
    if season_number is not None:
        params["seasonNumber"] = season_number
        params["name"] = "SeasonSearch"
    result = _make_api_request(f"command", method="POST", json=params)
    return result.get("status")

@mcp.tool()
def lookup_series(term: str) -> list[dict]:
    """Lookup series by a search term. Returns a list of series in library"""
    logging.info(f"Looking up series with term: {term}...")
    results = _make_api_request("series/lookup", params={"term": term})
    if isinstance(results, list):
        logging.info(f"Found {len(results)} series matching the term.")
        return [
            {
                "seriesId": r.get("id"),
                "status": r.get("status"),
                "title": r.get("title"),
                "year": r.get("year"),
                "seasons": r.get("seasons"),
                "monitored": r.get("monitored"),
                "monitorNewItems": r.get("monitorNewItems"),
            }
            for r in results if r.get("id") is not None
        ]
    else:
        logging.error("Failed to lookup series.")
        return []

@mcp.tool()
def get_episodes_by_series(series_id: int, season_number: int | None = None) -> list[dict]:
    """Get all episodes for a given series ID. Optionally filter by season number."""
    logging.info(f"Fetching episodes for series ID: {series_id}...")
    params = {
        "seriesId": series_id,
        "includeEpisodeFile": True
    }
    if season_number is not None:
        params["seasonNumber"] = season_number
    episodes = _make_api_request("episode", params=params)
    if isinstance(episodes, list):
        logging.info(f"Found {len(episodes)} episode(s) for series ID: {series_id}.")
        return [
            {
                "episodeId": e.get("id"),
                "airDate": e.get("airDate"),
                "seasonNumber": e.get("seasonNumber"),
                "episodeNumber": e.get("episodeNumber"),
                "episodeFileId": e.get("episodeFile").get("id") if e.get("episodeFile") else None,
                "episodeFileQuality": e.get("episodeFile").get("quality").get("quality").get("name") if e.get("episodeFile") else None,
                "title": e.get("title"),
                "monitored": e.get("monitored"),
                "hasFile": e.get("hasFile"),
            }
            for e in episodes
        ]
    else:
        logging.error("Failed to fetch episodes.")
        return []

@mcp.tool() 
def delete_episode_files(episode_file_ids: list[int]) -> dict:
    """Delete files for specific episodes by their episode IDs."""
    logging.info(f"Deleting files for episode IDs: {episode_file_ids}...")
    result = _make_api_request("episode/file", method="DELETE", json={
        "episodeIds": episode_file_ids
    })
    return result