# blackjack

Blackjack Simulator made with pygame

### Dev Install & Setup

```sh
git clone https://github.com/amiyuki7/blackjack.git
cd blackjack
source setup
```

Dev entrypoint: `python main.py`

### Alternatively...

```sh
pip install blackjack-amiyuki
```

and create a file like so and run it:

```py
# main.py

from blackjack import *
from blackjack.state.loading import Loading

if __name__ == "__main__":
    App(Loading).run()
```
