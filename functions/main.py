from firebase_functions import https_fn, options, params
from firebase_admin import initialize_app
import json
import asyncio

from rfi import get_departures, get_arrivals

initialize_app()

options.set_global_options(
  region=options.SupportedRegion.EUROPE_WEST1,
)

@https_fn.on_request(cors=options.CorsOptions(
  cors_origins="*",
  cors_methods=["get"],
))
def departures(req: https_fn.Request) -> https_fn.Response:
  station = req.args.get("station")
  if not station:
    raise https_fn.HttpsError(
      https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
      "Missing station code"
    )
  return https_fn.Response(
    json.dumps([{
      "carrier": {
        "alt": departure.carrier.alt,
        "src": departure.carrier.src
      },
      "category": {
        "alt": departure.category.alt,
        "src": departure.category.src
      },
      "trainNumber": departure.train_number,
      "terminus": departure.terminus,
      "time": departure.time,
      "delay": departure.delay,
      "platform": departure.platform,
      "approaching": departure.approaching,
      "info": departure.info
    } for departure in (asyncio.run(get_departures(station)))]),
    content_type="application/json"
  )

@https_fn.on_request(cors=options.CorsOptions(
  cors_origins="*",
  cors_methods=["get"],
))
def arrivals(req: https_fn.Request) -> https_fn.Response:
  station = req.args.get("station")
  if not station:
    raise https_fn.HttpsError(
      https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
      "Missing station code"
    )
  return https_fn.Response(
    json.dumps([{
      "carrier": {
        "alt": arrival.carrier.alt,
        "src": arrival.carrier.src
      } if arrival.carrier else None,
      "category": {
        "alt": arrival.category.alt,
        "src": arrival.category.src
      } if arrival.category else None,
      "trainNumber": arrival.train_number,
      "terminus": arrival.terminus,
      "time": arrival.time,
      "delay": arrival.delay,
      "platform": arrival.platform,
      "approaching": arrival.approaching,
      "info": arrival.info
    } for arrival in (asyncio.run(get_arrivals(station)))]),
    content_type="application/json"
  )