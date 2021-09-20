from app.utils.time import make_ordinal


class WhenMakingOrdinal:

    def it_returns_an_ordinal_correctly(self):
        ordinal = make_ordinal(11)
        assert ordinal == '11th'
