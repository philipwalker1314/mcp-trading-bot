class Portfolio:

    def __init__(self):

        self.positions = {}

    def add_position(
        self,
        symbol: str,
        data: dict,
    ):

        self.positions[symbol] = data

    def remove_position(
        self,
        symbol: str,
    ):

        if symbol in self.positions:
            del self.positions[symbol]

    def get_positions(self):

        return self.positions

    def total_positions(self):

        return len(self.positions)
