_DEFAULT_TERRA_GEOCRUD = {
    # default extent to world
    'EXTENT': [[-90.0, -180.0], [90.0, 180.0]],
    'STYLES': {
        'line': {
            'type': 'line',
            'paint': {
                'line-color': '#000',
                'line-width': 3
            }
        },
        'point': {
            'type': 'circle',
            'paint': {
                'circle-color': '#000',
                'circle-radius': 8
            }
        },
        'polygon': {
            'type': 'fill',
            'paint': {
                'fill-color': '#000'
            }
        },
    }
}

TERRA_GEOCRUD = _DEFAULT_TERRA_GEOCRUD
