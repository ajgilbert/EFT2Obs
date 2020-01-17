import json


def GetConfigFile(filename):
    with open(filename) as jsonfile:
        cfg = json.load(jsonfile)

    for p in cfg['parameters']:
        for k in cfg['parameter_defaults']:
            if k not in p:
                p[k] = cfg['parameter_defaults'][k]
    return cfg
