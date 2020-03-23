from Resources.Resources import Resource


class Bay(Resource):
    def __init__(self, position, parameter):
        Resource.__init__(self, position, parameter)

    def __str__(self):
        return "Bay"
