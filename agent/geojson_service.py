import json

def farm_to_geojson(coordinates_json):

    coords = json.loads(coordinates_json)

    polygon = []

    for point in coords[0]:
        polygon.append([
            point["lng"],
            point["lat"]
        ])

    # First point repeat to close polygon
    polygon.append(polygon[0])

    geojson = {
        "type": "Polygon",
        "coordinates": [polygon]
    }

    return geojson