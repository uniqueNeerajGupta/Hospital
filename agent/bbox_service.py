import json

def get_bbox(coordinates_json):

    coords = json.loads(coordinates_json)

    points = coords[0]

    lats = [point["lat"] for point in points]
    lngs = [point["lng"] for point in points]

    bbox = [
        min(lngs),
        min(lats),
        max(lngs),
        max(lats)
    ]

    return bbox ,,,,,,