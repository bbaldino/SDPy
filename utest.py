import unittest
import PyParsingSdpDefs as grammar
import Sdp as objects

def verify_line(test_obj, parsed_res, expected_line_data):
    expected_field_value_tuples = expected_line_data["fields"]
    for field, value in expected_field_value_tuples:
        if isinstance(value, dict):
            verify_line(test_obj, parsed_res[field], value)
        else:
            test_obj.assertIn(field, parsed_res, "Couldn't find %s in\n%s" % (field, parsed_res.dump()))
            if isinstance(value, list):
                # If it's a repeated field (instance of list) grab it asList so we get the raw list instead of the
                #  PyParseResults object
                test_obj.assertEqual(parsed_res[field].asList(), value)
            else:
                test_obj.assertEqual(parsed_res[field], value)

def verify_multi_line(test_obj, parsed_results, expected_lines_data):
    test_obj.assertEqual(len(parsed_results), len(expected_lines_data))
    for parsed_res, expected_line_data in zip(parsed_results, expected_lines_data):
        verify_line(test_obj, parsed_res, expected_line_data)

def verify_section(test_obj, parsed_res, expected_section_data):
    expected_field_value_tuples = expected_section_data["fields"]
    for field, line in expected_field_value_tuples:
        test_obj.assertIn(field, parsed_res, "Couldn't find %s in\n%s" % (field, parsed_res.dump()))
        if isinstance(line, list):
            verify_multi_line(test_obj, parsed_res[field], line)
        else:
            verify_line(test_obj, parsed_res[field], line)

def build_line_str(line_data):
    prefix = line_data["prefix"]
    fields = line_data["fields"]
    join_token = line_data["join_token"] if "join_token" in line_data else " "
    # We may have a line that has a 'meta-field' (a "line within a line").  Mainly this is the case for a= lines
    #  TODO: for now we'll assume the presence of at least one meta-field implies that there are no normal fields
    #   (so far that's all I've seen)
    meta_fields = [field_value for field_name, field_value in fields if isinstance(field_value, dict)]
    if meta_fields:
        return prefix + (join_token.join(build_line_str(sub_field) for sub_field in meta_fields))
    else:
        # A line may have a repeated sub-field, if so: detect it and join the values with spaces
        def check_for_repeated(field):
            if isinstance(field, list):
                return " ".join(field_sub_value for field_sub_value in field_value)
            else:
                return field
        # Check each value and call check_for_repeated to check if one of them is a repeated field, if so,
        #  check_for_repeated will detect it and concatenate it into a single string for us
        return prefix + join_token.join(map(check_for_repeated, [field[1] for field in fields]))

def build_section_str(section_data):
    fields = section_data["fields"]
    str = ""
    for field in fields:
        if isinstance(field[1], list):
            # multi-line field
            for sub_field in field[1]:
                str += (build_line_str(sub_field) + "\n")
        else:
            str += build_line_str(field[1])
        str += "\n"
    return str

def parse_and_verify_line(test_obj, line_grammar, line_data):
    res = line_grammar.parseString(build_line_str(line_data))
    res = res[0]
    verify_line(test_obj, res, line_data)

def parse_and_test_section(test_obj, section_grammar, section_data):
    res = section_grammar.parseString(build_section_str(section_data))
    verify_section(test_obj, res, section_data)

# Some sample values for each of the line types
class SampleData(object):
    vline_data = {"prefix": "v=",
                  "fields": [("VERSION_NUMBER", "0")]
                 }
    oline_data = {"prefix": "o=",
                  "fields": [("USERNAME", "-"), 
                             ("SESSION_ID", "4143029973181426116"), 
                             ("SESSION_VERSION", "2"),
                             ("NETTYPE", "IN"),
                             ("ADDRTYPE", "IP4"),
                             ("IP_ADDR", "127.0.0.1")]}
    sline_data = {"prefix": "s=",
                  "fields": [("SESSION_NAME", "-")]}
    iline_data = {"prefix": "i=",
                  "fields": [("SESSION_INFORMATION", "Test Session")]}
    cline_data = {"prefix": "c=",
                  "fields": [("NETTYPE", "IN"),
                             ("ADDRTYPE", "IP4"),
                             ("IP_ADDR", "127.0.0.1")]}
    bline_data = {"prefix": "b=",
                  "join_token": ":",
                  "fields": [("BWTYPE", "AS"),
                             ("BW", "128")]}
    tline_data = {"prefix": "t=",
                  "fields": [("START_TIME", "1234567"),
                             ("STOP_TIME", "2345678")]}



class TestLineParsing(unittest.TestCase):
    def test_parse_version_line(self):
        parse_and_verify_line(self, grammar.version_line, SampleData.vline_data)

    def test_parse_originator_line(self):
        parse_and_verify_line(self, grammar.originator_line, SampleData.oline_data)

    def test_parse_session_name_line(self):
        parse_and_verify_line(self, grammar.session_name_line, SampleData.sline_data)

    def test_parse_session_information_line(self):
        parse_and_verify_line(self, grammar.session_information_line, SampleData.iline_data)

    def test_parse_connection_information_line(self):
        parse_and_verify_line(self, grammar.connection_information_line, SampleData.cline_data)

    def test_parse_bandwidth_information_line(self):
        parse_and_verify_line(self, grammar.bandwidth_information_line, SampleData.bline_data)

    def test_parse_time_description_line(self):
        parse_and_verify_line(self, grammar.time_description_line, SampleData.tline_data)

    def test_parse_generic_application_line(self):
        aline_data = {"prefix": "a=",
                      "fields": [("GENERIC_APPLICATION_LINE", "some unknown generic line")]}
        
        parse_and_verify_line(self, grammar.application_line, aline_data)

    def test_parse_direction_application_line(self):
        aline_data = {"prefix": "a=",
                      "fields": [("DIRECTION_APPLICATION_LINE", {"prefix": "",
                                                                 "fields": [("DIRECTION", "sendrecv")]})]}
         
        parse_and_verify_line(self, grammar.application_line, aline_data)

    def test_parse_rtcp_application_line(self):
        aline_data = {"prefix": "a=",
                      "fields": [("RTCP_APPLICATION_LINE", {"prefix": "rtcp:",
                                                            "fields": [("PORT", "1"),
                                                                       ("NETTYPE", "IN"),
                                                                       ("ADDRTYPE", "IP4"),
                                                                       ("IP_ADDR", "127.0.0.1")]})]}

        parse_and_verify_line(self, grammar.application_line, aline_data)

    def test_parse_media_description_line(self):
        mline_data = {"prefix": "m=",
                      "fields": [("MEDIA_TYPE", "audio"),
                                 ("PORT", "0"),
                                 ("PROTO", "RTP/SAVPF"),
                                 ("FORMATS", ["111", "222", "333", "444"])]}

        parse_and_verify_line(self, grammar.media_description_line, mline_data)

class TestSectionParsing(unittest.TestCase):
    def test_parse_session_section(self):
        vline_data = {"prefix": "v=",
                      "fields": [("VERSION_NUMBER", "0")]
                     }

        oline_data = {"prefix": "o=",
                      "fields": [("USERNAME", "-"), 
                                 ("SESSION_ID", "4143029973181426116"), 
                                 ("SESSION_VERSION", "2"),
                                 ("NETTYPE", "IN"),
                                 ("ADDRTYPE", "IP4"),
                                 ("IP_ADDR", "127.0.0.1")]}

        sline_data = {"prefix": "s=",
                      "fields": [("SESSION_NAME", "-")]}

        iline_data = {"prefix": "i=",
                      "fields": [("SESSION_INFORMATION", "Test Session")]}

        cline_data = {"prefix": "c=",
                      "fields": [("NETTYPE", "IN"),
                                 ("ADDRTYPE", "IP4"),
                                 ("IP_ADDR", "127.0.0.1")]}

        bline_data = {"prefix": "b=",
                      "join_token": ":",
                      "fields": [("BWTYPE", "AS"),
                                 ("BW", "128")]}

        tline_data = {"prefix": "t=",
                      "fields": [("START_TIME", "1234567"),
                                 ("STOP_TIME", "2345678")]}

        generic_aline_data = {"prefix": "a=",
                              "fields": [("GENERIC_APPLICATION_LINE", "some unknown generic line")]}

        direction_aline_data = {"prefix": "a=",
                                "fields": [("DIRECTION_APPLICATION_LINE", {"prefix": "",
                                                                           "fields": [("DIRECTION", "sendrecv")]})]}

        rtcp_aline_data = {"prefix": "a=",
                           "fields": [("RTCP_APPLICATION_LINE", {"prefix": "rtcp:",
                                                                 "fields": [("PORT", "1"),
                                                                            ("NETTYPE", "IN"),
                                                                            ("ADDRTYPE", "IP4"),
                                                                            ("IP_ADDR", "127.0.0.1")]})]}

        session_section_data = {"fields": [("VERSION_LINE", vline_data),
                                           ("ORIGINATOR_LINE", oline_data),
                                           ("SESSION_NAME_LINE", sline_data),
                                           ("SESSION_INFORMATION_LINE", iline_data),
                                           ("CONNECTION_INFORMATION_LINE", cline_data),
                                           ("BANDWIDTH_INFORMATION_LINES", [bline_data]),
                                           ("TIME_DESCRIPTION_LINES", [tline_data]),
                                           ("APPLICATION_LINES", [generic_aline_data, direction_aline_data, rtcp_aline_data])]}

        parse_and_test_section(self, grammar.session_section, session_section_data)

    def test_parse_media_section(self):
        mline_data = {"prefix": "m=",
                      "fields": [("MEDIA_TYPE", "audio"),
                                 ("PORT", "0"),
                                 ("PROTO", "RTP/SAVPF"),
                                 ("FORMATS", ["111", "222", "333", "444"])]}

        iline_data = {"prefix": "i=",
                      "fields": [("SESSION_INFORMATION", "Test Session")]}

        cline_data = {"prefix": "c=",
                      "fields": [("NETTYPE", "IN"),
                                 ("ADDRTYPE", "IP4"),
                                 ("IP_ADDR", "127.0.0.1")]}

        bline_data = {"prefix": "b=",
                      "join_token": ":",
                      "fields": [("BWTYPE", "AS"),
                                 ("BW", "128")]}

        generic_aline_data = {"prefix": "a=",
                              "fields": [("GENERIC_APPLICATION_LINE", "some unknown generic line")]}

        direction_aline_data = {"prefix": "a=",
                                "fields": [("DIRECTION_APPLICATION_LINE", {"prefix": "",
                                                                           "fields": [("DIRECTION", "sendrecv")]})]}

        rtcp_aline_data = {"prefix": "a=",
                           "fields": [("RTCP_APPLICATION_LINE", {"prefix": "rtcp:",
                                                                 "fields": [("PORT", "1"),
                                                                            ("NETTYPE", "IN"),
                                                                            ("ADDRTYPE", "IP4"),
                                                                            ("IP_ADDR", "127.0.0.1")]})]}

        media_section_data = {"fields": [("MEDIA_DESCRIPTION_LINE", mline_data),
                                         ("SESSION_INFORMATION_LINE", iline_data),
                                         ("BANDWIDTH_INFORMATION_LINES", [bline_data]),
                                         ("APPLICATION_LINES", [generic_aline_data, direction_aline_data, rtcp_aline_data])]}

        parse_and_test_section(self, grammar.media_section, media_section_data)

def verify_line_object(test_obj, line_object, expected_data):
    for field_name, field_value in expected_data["fields"]:
        print("looking at field_name %s and filed_value %s" % (field_name, field_value))
        # Meta-line
        if isinstance(field_value, dict):
            verify_line_object(test_obj, getattr(line_object, field_name.lower()), field_value)
        else:
            test_obj.assertEqual(field_value, getattr(line_object, field_name.lower()))

def build_and_verify_line_object(test_obj, line_obj_type, line_grammar, line_data):
    line_str = build_line_str(line_data)
    res = line_grammar.parseString(line_str)
    res = res[0]
    obj = line_obj_type(res)
    verify_line_object(test_obj, obj, line_data)

class TestObjectCreation(unittest.TestCase):
    def test_create_version_line_object(self):
        build_and_verify_line_object(self, objects.VersionLine, grammar.version_line, SampleData.vline_data)

    def test_create_originator_line_object(self):
        build_and_verify_line_object(self, objects.OriginatorLine, grammar.originator_line, SampleData.oline_data)

    def test_create_session_name_line_object(self):
        build_and_verify_line_object(self, objects.SessionNameLine, grammar.session_name_line, SampleData.sline_data)

    def test_create_session_information_line_object(self):
        build_and_verify_line_object(self, objects.SessionInformationLine, grammar.session_information_line, SampleData.iline_data)

    def test_create_connection_information_line_object(self):
        build_and_verify_line_object(self, objects.ConnectionInformationLine, grammar.connection_information_line, SampleData.cline_data)

    def test_create_bandwidth_information_line_object(self):
        build_and_verify_line_object(self, objects.BandwidthInformationLine, grammar.bandwidth_information_line, SampleData.bline_data)

    def test_create_time_description_line_object(self):
        build_and_verify_line_object(self, objects.TimeDescriptionLine, grammar.time_description_line, SampleData.tline_data)

    def test_create_generic_application_line_object(self):
        aline_data = {"prefix": "a=",
                      "fields": [("GENERIC_APPLICATION_LINE", "some unknown generic line")]}
        build_and_verify_line_object(self, objects.ApplicationLine, grammar.application_line, aline_data)

    def test_create_direction_application_line_object(self):
        aline_data = {"prefix": "a=",
                      "fields": [("DIRECTION_APPLICATION_LINE", {"prefix": "",
                                                                 "fields": [("DIRECTION", "sendrecv")]})]}
        build_and_verify_line_object(self, objects.ApplicationLine, grammar.application_line, aline_data)

if __name__ == '__main__':
    unittest.main()
