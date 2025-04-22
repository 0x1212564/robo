class Persoon:
    def __init__(self, naam):
        self.__naam = naam
        pass

    def get_naam(self):
        return self.__naam

    def set_naam(self, naam):
        self.naam = naam
        
p  = Persoon('Alice')
p.set_naam('Bob')

print(p.get_naam())
