from IdeaSim.Resources import Resource


class Bay(Resource):
    def __init__(self, sim, position):
        Resource.__init__(self, sim)
        self.position = position

    def __str__(self):
        return "Bay"
