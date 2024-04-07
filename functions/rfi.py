import requests
import asyncio

from dataclasses import dataclass
from bs4 import BeautifulSoup
from logging import Logger

logger = Logger("RFI Scraper")

STATIONS_URL = "https://iechub.rfi.it/ArriviPartenze"
MONITOR_URL = "https://iechub.rfi.it/ArriviPartenze/ArrivalsDepartures/Monitor"
DEFAULT_HEADERS = {
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
  "Referer": "https://www.google.com"
}

@dataclass
class RFIStation:
  name: str
  _id: str

@dataclass
class ImageDescriptor:
  alt: str
  src: str

@dataclass
class RFIMonitorEntry:
  carrier: ImageDescriptor
  category: ImageDescriptor
  train_number: str
  terminus: str
  time: str
  delay: str
  platform: str
  approaching: bool
  info: str

async def get_stations() -> list[RFIStation]:
  try:
    f = requests.get(STATIONS_URL, headers=DEFAULT_HEADERS)
  except Exception as e:
    logger.error(f"Could not get stations list: {e!r}")
    return None
  page = f.text
  soup = BeautifulSoup(page, 'html.parser')
  select = soup.select_one("#ElencoLocalita")
  if not select:
    logger.error(f"Could not parse stations list: {e!r}")
    return None
  return [RFIStation(
    name=option.get_text(),
    _id=option["value"]
  ) for option in select.select("option")]

async def get_monitor(place_id: str, direction: str) -> list[RFIMonitorEntry]:
  try:
    f = requests.get(MONITOR_URL, params={
      "Arrivals": "False" if direction == "D" else "True",
      "PlaceId": place_id
    }, headers=DEFAULT_HEADERS)
  except Exception as e:
    logger.error(f"Could not get monitor for {place_id}: {e!r}")
    return None
  page = f.text
  soup = BeautifulSoup(page, 'html.parser')
  monitor = soup.select_one("#monitor")
  if not monitor:
    logger.error(f"Could not parse monitor for {place_id}: {e!r}")
    return None
  return [RFIMonitorEntry(
    carrier=ImageDescriptor(
      alt=tr.select_one("#RVettore img")["alt"],
      src=tr.select_one("#RVettore img")["src"]
    ) if tr.select_one("#RVettore img") else None,
    category=ImageDescriptor(
      alt=tr.select_one("#RCategoria img")["alt"],
      src=tr.select_one("#RCategoria img")["src"]
    ) if tr.select_one("#RCategoria img") else None,
    train_number=tr.select_one("#RTreno").get_text().strip(),
    terminus=tr.select_one("#RStazione").get_text().strip(),
    time=tr.select_one("#ROrario").get_text().strip(),
    delay=tr.select_one("#RRitardo").get_text().strip(),
    platform=tr.select_one("#RBinario").get_text().strip(),
    approaching=tr.select_one("#RExLampeggio img") != None,
    info=tr.select_one(
      "#RDettagli .testoinfoaggiuntive"
    ).get_text().strip() if tr.select_one("#RDettagli .testoinfoaggiuntive") else None
  ) for tr in monitor.select("tr[id]")]

async def get_departures(place_id: str) -> list[RFIMonitorEntry]:
  return await get_monitor(place_id, "D")

async def get_arrivals(place_id: str) -> list[RFIMonitorEntry]:
  return await get_monitor(place_id, "A")