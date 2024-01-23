import filetype

# Hack to suport SVG files
# Are there any other files that filetype doesn't natively recognise?
class Svg(filetype.Type):
    MIME = 'image/svg+xml'
    EXTENSION = 'svg'

    def __init__(self):
        super(Svg, self).__init__(
            mime = Svg.MIME,
            extension = Svg.EXTENSION
            )

    def match(self, buf):
        return False
