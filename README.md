# OpenABIS FingerjetFX Plugin

OpenABIS' plugin for [FingerJetFXOSE/FingerJetFXOSE](https://github.com/FingerJetFXOSE/FingerJetFXOSE)

## Installation

**Pipenv**
```
pipenv install git+https://github.com/openabis/openabis-fingerjetfx.git@master#openabis_fingerjetfx
```

**Pip**
```
pip install git+https://github.com/openabis/openabis-fingerjetfx.git@master
```

## Usage
`FingerjetExtractor` can be readily imported after successful installation. It accepts a `config` dictionary that
includes the following: 

FINGERJET_MAX_MINUTIAE(int) - maximum minutiae
DEFAULT_FINGERPRINT_DPI(int) - fingerprint image dpi
