from SdpDefs import SdpTerms
from PyParsingSdpDefs import sdp_def

# ------ PyParsing-related base classes ------

# Parse a single line.  Just take the fields and assign them as member variables
class PyParsedLine(object):
    def __init__(self, parsed_line):
        print("PARSING LINE: %s" % parsed_line)
        for field in parsed_line.keys():
            setattr(self, field.lower(), parsed_line[field])

    def to_string(self, prefix=""):
        str = ""
        for var in vars(self).keys():
            str += "%s%s: %s\n" % (prefix, var, getattr(self, var))
        return str

# Used for lines that have lines 'within' them (application lines).  This is basically to handle a line
#  that isn't parsed as just a dictionary (the bottom of the chain) but is still a ParseResults object
class PyParsedMetaLine(object):
    def __init__(self, parsed_line):
        print("PARSING META LINE: %s" % parsed_line.asDict())
        # Only 1 level of meta
        assert len(parsed_line.keys()) == 1
        sub_line_name = parsed_line.keys()[0]
        sub_line = parsed_line[sub_line_name]
        
        #if sub_line_name == "GENERIC_APPLICATION_LINE": # TODO: should only be necessary until we have parsing for all application field sub-types (?)
        #    setattr(self, sub_line_name.lower(), SdpObjectMapping[sub_line_name]({"content": sub_line}))
        #else:
        #    setattr(self, sub_line_name.lower(), SdpObjectMapping[sub_line_name](sub_line))
        setattr(self, sub_line_name.lower(), SdpObjectMapping[sub_line_name](sub_line))

    def to_string(self, prefix=""):
        str = ""
        for var in vars(self).keys():
            str += getattr(self, var).to_string(prefix)
        return str

# Used for lines that may be repeated more than once.  Takes the 'single line' type so that it can
#  create an instance of it for each line
class PyParsedMultiLine(object):
    def __init__(self, sub_line_type, parsed_lines):
        self.sub_lines = []
        for line in parsed_lines:
            self.sub_lines.append(sub_line_type(line))

    def to_string(self, prefix=""):
        str = ""
        for i, line in enumerate(self.sub_lines):
            str += "%sline %d:\n%s" % (prefix, i, line.to_string(prefix + "  "))
        return str

class PyParsedSection(object):
    def __init__(self, parsed_section, fields):
        for field in fields:
            if field in parsed_section:
                setattr(self, field.lower(), SdpObjectMapping[field](parsed_section[field]))
            else:
                print("Field missing: %s" % field)

    def to_string(self, prefix="", field_order=None):
        fields = field_order if field_order else vars(self).keys()
        str = ""
        for field in fields:
            if hasattr(self, field):
                str += "%s%s:\n%s\n" % (prefix, field, getattr(self, field).to_string(prefix + "  "))
        return str

class PyParsedMultiSection(object):
    def __init__(self, sub_section_type, parsed_sections):
        self.sub_sections = []
        for section in parsed_sections:
            print("looking at multi sub section:\n%s" % section.asDict())
            self.sub_sections.append(sub_section_type(section))

    def to_string(self, prefix=""):
        str = ""
        for i, section in enumerate(self.sub_sections):
            str += "%ssection %d:\n%s" % (prefix, i, section.to_string(prefix + "  "))
        return str


# ------ SDP Line classes ------

class VersionLine(PyParsedLine):
    pass

class OriginatorLine(PyParsedLine):
    pass

class SessionNameLine(PyParsedLine):
    pass

class SessionInformationLine(PyParsedLine):
    pass

class UriLine(PyParsedLine):
    pass

class EmailAddressLine(PyParsedLine):
    pass

class PhoneNumberLine(PyParsedLine):
    pass

class ConnectionInformationLine(PyParsedLine):
    pass

class BandwidthInformationLine(PyParsedLine):
    pass

class BandwidthInformationLines(PyParsedMultiLine):
    def __init__(self, parsed_lines):
        super(BandwidthInformationLines, self).__init__(BandwidthInformationLine, parsed_lines)

class TimeDescriptionLine(PyParsedLine):
    pass

class TimeDescriptionLines(PyParsedMultiLine):
    def __init__(self, parsed_lines):
        super(TimeDescriptionLines, self).__init__(TimeDescriptionLine, parsed_lines)

class DirectionApplicationLine(PyParsedLine):
    pass

class RtcpApplicationLine(PyParsedLine):
    pass

class GenericApplicationLine(PyParsedLine):
    pass

class ApplicationLine(PyParsedMetaLine):
    pass

class ApplicationLines(PyParsedMultiLine):
    def __init__(self, parsed_lines):
        super(ApplicationLines, self).__init__(ApplicationLine, parsed_lines)

class MediaDescriptionLine(PyParsedLine):
    pass

# ------ SDP section classes ------
class SessionSection(PyParsedSection):
    fields = [SdpTerms.VERSION_LINE, SdpTerms.ORIGINATOR_LINE, SdpTerms.SESSION_NAME_LINE, SdpTerms.SESSION_INFORMATION_LINE, 
              SdpTerms.URI_LINE, SdpTerms.EMAIL_ADDRESS_LINE, SdpTerms.PHONE_NUMBER_LINE, SdpTerms.CONNECTION_INFORMATION_LINE,
              SdpTerms.BANDWIDTH_INFORMATION_LINES, SdpTerms.TIME_DESCRIPTION_LINES, SdpTerms.APPLICATION_LINES]
    def __init__(self, parsed_session_section):
        super(SessionSection, self).__init__(parsed_session_section, SessionSection.fields)

    def to_string(self, prefix=""):
        return super(SessionSection, self).to_string(prefix, [x.lower() for x in SessionSection.fields])

class MediaSection(PyParsedSection):
    fields = [SdpTerms.MEDIA_DESCRIPTION_LINE, SdpTerms.SESSION_INFORMATION_LINE, SdpTerms.CONNECTION_INFORMATION_LINE,
              SdpTerms.BANDWIDTH_INFORMATION_LINES, SdpTerms.APPLICATION_LINES]
    def __init__(self, parsed_media_section):
        super(MediaSection, self).__init__(parsed_media_section, MediaSection.fields)

    def to_string(self, prefix=""):
        return super(MediaSection, self).to_string(prefix, [x.lower() for x in MediaSection.fields])

class MediaSections(PyParsedMultiSection):
    def __init__(self, parsed_media_sections):
        super(MediaSections, self).__init__(MediaSection, parsed_media_sections)
    
# ------ SDP top level class ------
import pprint
pp = pprint.PrettyPrinter(indent=4)
class Sdp:
    fields = [SdpTerms.SESSION_SECTION, SdpTerms.MEDIA_SECTIONS]
    def __init__(self, sdp_string):
        res = sdp_def.parseString(sdp_string)
        #print("Second media section:")
        #pp.pprint(res["MEDIA_SECTIONS"][1].asDict())
        for field in Sdp.fields:
            setattr(self, field.lower(), SdpObjectMapping[field](res[field]))
        print(self.to_string())

    def to_string(self, prefix=""):
        str = ""
        for field in Sdp.fields:
            if hasattr(self, field.lower()):
                str += "%s:\n%s\n" % (field, getattr(self, field.lower()).to_string("  "))
        return str
        

# Map Sdp terms to their corresponding object
SdpObjectMapping = {SdpTerms.VERSION_LINE: VersionLine,
                    SdpTerms.ORIGINATOR_LINE: OriginatorLine,
                    SdpTerms.SESSION_NAME_LINE: SessionNameLine,
                    SdpTerms.SESSION_INFORMATION_LINE: SessionInformationLine,
                    SdpTerms.URI_LINE: UriLine,
                    SdpTerms.EMAIL_ADDRESS_LINE: EmailAddressLine,
                    SdpTerms.PHONE_NUMBER_LINE: PhoneNumberLine,
                    SdpTerms.CONNECTION_INFORMATION_LINE: ConnectionInformationLine,
                    SdpTerms.BANDWIDTH_INFORMATION_LINES: BandwidthInformationLines,
                    SdpTerms.TIME_DESCRIPTION_LINES: TimeDescriptionLines,
                    SdpTerms.APPLICATION_LINES: ApplicationLines,
                    SdpTerms.DIRECTION_APPLICATION_LINE: DirectionApplicationLine,
                    SdpTerms.RTCP_APPLICATION_LINE: RtcpApplicationLine,
                    SdpTerms.GENERIC_APPLICATION_LINE: GenericApplicationLine,
                    SdpTerms.MEDIA_DESCRIPTION_LINE: MediaDescriptionLine,
                    SdpTerms.SESSION_SECTION: SessionSection,
                    SdpTerms.MEDIA_SECTIONS: MediaSections}
