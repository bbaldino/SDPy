from pyparsing import *
from SdpDefs import SdpTerms

# Generic types
number = Word(nums) 
nettype = Literal("IN").setName("NETTYPE")
addrtype = (Literal("IP4") | Literal("IP6")).setName("ADDRTYPE")
octet = Word(nums, max=3)
ip_addr = Combine(octet + Literal(".") + octet + Literal(".") + octet + Literal(".") + octet).setName("IP_ADDR")
port = number.setName("PORT")

# ---- Version line ----
# Prefix
version_line_prefix = Suppress(Literal("v=").setName("VLINE_PREFIX"))
# Fields
version_number = number.setName("VERSION_NUMBER")
# Line
version_line = Group(version_line_prefix + version_number("VERSION_NUMBER")).setName(SdpTerms.VERSION_LINE)

# ---- Originator line ----
# Prefix
originator_line_prefix = Suppress(Literal("o=").setName("OLINE_PREFIX"))
# Fields
username = Word(alphanums + "-").setName("USERNAME")
session_id = number.setName("SESSION_ID")
session_version = number.setName("SESSION_VERSION")
# Line
originator_line = Group(originator_line_prefix + username("USERNAME") + session_id("SESSION_ID") + session_version("SESSION_VERSION") + nettype("NETTYPE") + addrtype("ADDRTYPE") + ip_addr("IP_ADDR")).setName(SdpTerms.ORIGINATOR_LINE)

# ---- Session Name line ----
# Prefix
session_name_line_prefix = Suppress(Literal("s=")).setName("SLINE_PREFIX")
# Fields
session_name = (Word(alphanums + "-") | White()).setName("SESSION_NAME")
# Line
session_name_line = Group(session_name_line_prefix + session_name("SESSION_NAME")).setName(SdpTerms.SESSION_NAME_LINE)

# ---- Session Information line ----
# Prefix
session_information_line_prefix = Suppress(Literal("i=")).setName("SESSION_INFORMATION_LINE_PREFIX")
# Fields
session_information = (Word(alphanums + "- ") | White()).setName("SESSION_INFORMATION")
# Line
session_information_line = Group(session_information_line_prefix + session_information("SESSION_INFORMATION")).setName(SdpTerms.SESSION_INFORMATION_LINE)

# ---- URI line ----
# TODO
uri_line = Literal("u=").setName(SdpTerms.URI_LINE)

# ---- Email Address line ----
# TODO
email_address_line = Literal("e=").setName(SdpTerms.EMAIL_ADDRESS_LINE)

# ---- Phone Number line ----
# TODO
phone_number_line = Literal("p=").setName(SdpTerms.PHONE_NUMBER_LINE)

# ---- Connection Information line ----
# Prefix
connection_information_line_prefix = Suppress(Literal("c=")).setName("CONNECTION_INFORMATION_LINE_PREFIX")
# Line
connection_information_line = Group(connection_information_line_prefix + nettype("NETTYPE") + addrtype("ADDRTYPE") + ip_addr("IP_ADDR")).setName(SdpTerms.CONNECTION_INFORMATION_LINE)

# ---- Bandwidth Information line ----
# Prefix
bandwidth_information_line_prefix = Suppress(Literal("b="))
# Fields
bwtype = (Literal("CT") | Literal("AS")).setName("BW_TYPE")
bw = number.setName("BW")
# Line
bandwidth_information_line = Group(bandwidth_information_line_prefix + bwtype("BWTYPE") + Literal(":") + bw("BW")).setName("BW_INFORMATION_LINE")

# ---- Time Description line ----
# Prefix
time_description_line_prefix = Suppress(Literal("t="))
# Fields
timestamp = number.setName("TIMESTAMP")
# Line
time_description_line = Group(time_description_line_prefix + timestamp("START_TIME") + timestamp("STOP_TIME")).setName("TIME_DESCRIPTION_LINE")

# ---- Application line ----
# Prefix
application_line_prefix = Suppress(Literal("a="))
# Fields (specific versions of known a lines and a catchall)
# Direction line
direction = (Literal("sendonly") | Literal("sendrecv") | Literal("recvonly")).setName("DIRECTION")
application_line_direction = Group(direction("DIRECTION").setName("APPLICATION_LINE_DIRECTION"))
# Rtcp Line
application_line_rtcp = Group(Suppress(Literal("rtcp:").setName("APPLICATION_LINE_RTCP_PREFIX")) + port("PORT") + Optional(nettype("NETTYPE")) + Optional(addrtype("ADDRTYPE")) + Optional(ip_addr("IP_ADDR")))
# ice-ufrag
application_line_ice_ufrag = Group(Suppress(Literal("ice-ufrag:").setName("APPLICATION_LINE_ICE_UFRAG_PREFIX")) + Word(alphanums + "+")("USERNAME"))
# ice-pwd
application_line_ice_pwd = Group(Suppress(Literal("ice-pwd:").setName("APPLICATION_LINE_ICE_PWD_PREFIX")) + Word(alphanums + "+")("PASSWORD"))
# group
application_line_group = Group(Suppress(Literal("group:").setName("APPLICATION_LINE_GROUP_PREFIX")) + Word(alphanums)("PURPOSE") + OneOrMore(Word(alphanums).setResultsName("IDS", listAllMatches=True)))
# mid
application_line_mid = Group(Suppress(Literal("mid:").setName("APPLICATION_LINE_MID_PREFIX")) + Word(alphanums)("ID"))
# rtcp-mux
application_line_rtcp_mux = Group(Literal("rtcp-mux")("RTCP_MUX").setName("APPLICATION_LINE_RTCP_MUX"))
# rtpmap
#TODO: it's tempting to 'group' the encoding name/clock rate/encoding parameters but, since it then creates a list of parse results, it's a bit hard to detect
# when parsing things.  (it would show up as a list, which currently we detect as a repeated field, so we'd need to check that it was ParseResults objects in
# the list and then know it was a grouped sub-field.  Will look into that as a possibility later if we really need it...)  Hmmm...this causes problems because then
# the object gets duplicate member variables in the wrong places...
application_line_rtpmap = Group(Suppress(Literal("rtpmap:").setName("APPLICATION_LINE_RTPMAP_PREFIX")) + 
                                number("PT") + 
                                Group(Word(alphanums)("ENCODING_NAME") + 
                                      Suppress(Literal("/")) + 
                                      number("CLOCK_RATE") + 
                                      Optional(Suppress(Literal("/")) + 
                                      restOfLine("ENCODING_PARAMETERS")))("RTPMAP_CODEC_INFO"))
# Generic app line
application_line_generic = Group(restOfLine("CONTENT").setName("APPLICATION_LINE_GENERIC"))
# Line
application_line = Group(application_line_prefix + (application_line_direction(SdpTerms.DIRECTION_APPLICATION_LINE) | 
                                                    application_line_rtcp(SdpTerms.RTCP_APPLICATION_LINE) | 
                                                    application_line_ice_ufrag(SdpTerms.ICE_UFRAG_APPLICATION_LINE) |
                                                    application_line_ice_pwd(SdpTerms.ICE_PWD_APPLICATION_LINE) |
                                                    application_line_group(SdpTerms.GROUP_APPLICATION_LINE) |
                                                    application_line_mid(SdpTerms.MID_APPLICATION_LINE) |
                                                    application_line_rtpmap(SdpTerms.RTPMAP_APPLICATION_LINE) |
                                                    application_line_rtcp_mux(SdpTerms.RTCP_MUX_APPLICATION_LINE) |
                                                    application_line_generic(SdpTerms.GENERIC_APPLICATION_LINE)).setName("APPLICATION_LINE"))

# ---- Media Description line ----
# Prefix
media_description_line_prefix = Suppress(Literal("m="))
# Fields
media_type = (Literal("audio") | Literal("video") | Literal("text") | Literal("application") | Literal("message")).setName("MEDIA_TYPE")
# NOTE: Had to put "RTP/SAVPF" in front of "RTP/SAVP" or else the latter will take the match (even if the string is "RTP/SAVPF") Wonder if there's a way around that...
proto = (Literal("udp") | Literal("RTP/AVP") | Literal("RTP/SAVPF") | Literal("RTP/SAVP")).setName("PROTO")
fmt = number.setName("FORMAT")
# Line
media_description_line = Group(media_description_line_prefix + media_type("MEDIA_TYPE") + port("PORT") + proto("PROTO") + OneOrMore(fmt.setResultsName("FORMATS", listAllMatches=True))).setName(SdpTerms.MEDIA_DESCRIPTION_LINE)

# ---- Session section ----
session_section = version_line(SdpTerms.VERSION_LINE) + \
                  originator_line(SdpTerms.ORIGINATOR_LINE) + \
                  session_name_line(SdpTerms.SESSION_NAME_LINE) + \
                  Optional(session_information_line(SdpTerms.SESSION_INFORMATION_LINE)) + \
                  Optional(uri_line(SdpTerms.URI_LINE)) + \
                  Optional(email_address_line(SdpTerms.EMAIL_ADDRESS_LINE)) + \
                  Optional(phone_number_line(SdpTerms.PHONE_NUMBER_LINE)) + \
                  Optional(connection_information_line(SdpTerms.CONNECTION_INFORMATION_LINE)) + \
                  ZeroOrMore(bandwidth_information_line.setResultsName(SdpTerms.BANDWIDTH_INFORMATION_LINES, listAllMatches=True)) + \
                  OneOrMore(time_description_line.setResultsName(SdpTerms.TIME_DESCRIPTION_LINES, listAllMatches=True)) + \
                  ZeroOrMore(application_line.setResultsName(SdpTerms.APPLICATION_LINES, listAllMatches=True))

# ---- Media section ----
media_section = media_description_line(SdpTerms.MEDIA_DESCRIPTION_LINE) + \
                Optional(session_information_line(SdpTerms.SESSION_INFORMATION_LINE)) + \
                Optional(connection_information_line(SdpTerms.CONNECTION_INFORMATION_LINE)) + \
                ZeroOrMore(bandwidth_information_line.setResultsName(SdpTerms.BANDWIDTH_INFORMATION_LINES, listAllMatches=True)) + \
                ZeroOrMore(application_line.setResultsName(SdpTerms.APPLICATION_LINES, listAllMatches=True))


# ---- SDP ----
sdp = session_section(SdpTerms.SESSION_SECTION) + \
      ZeroOrMore(media_section.setResultsName(SdpTerms.MEDIA_SECTIONS, listAllMatches=True))
