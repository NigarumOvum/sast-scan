import importlib
import json
import os
import tempfile
import uuid
from pathlib import Path

import lib.convert as convertLib
import lib.issue as issueLib


def test_nodejsscan_convert_empty():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report("nodejsscan", [], ".", {}, {}, [], cfile.name)
        jsondata = json.loads(data)
        assert (
            jsondata["runs"][0]["automationDetails"]["description"]["text"]
            == "Static Analysis Security Test results using @ShiftLeft/sast-scan"
        )
        assert uuid.UUID(jsondata["inlineExternalProperties"][0]["guid"]).version == 4
        assert not jsondata["runs"][0]["results"]
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "total": 0,
            "critical": 0,
            "high": 0,
            "low": 0,
            "medium": 0,
        }


def test_nodejsscan_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "nodejsscan",
            [],
            ".",
            {},
            {},
            [
                {
                    "description": "MD5 is a a weak hash which is known to have collision. Use a strong hashing function.",
                    "filename": "InsufficientPasswordHash.js",
                    "line": 3,
                    "lines": 'function hashPassword(password) {\n    var crypto = require("crypto");\n    var hasher = crypto.createHash(\'md5\');\n    var hashed = hasher.update(password).digest("hex"); // BAD\n    return hashed;\n}',
                    "path": "/github/workspace/CWE-916/examples/InsufficientPasswordHash.js",
                    "sha2": "bfc3a2dfec54a8e77e41c3e3d7a6d87477ea1ed6d1cb3b1b60b8e135b0d18368",
                    "tag": "node",
                    "title": "Weak Hash used - MD5",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert (
            jsondata["runs"][0]["results"][0]["message"]["text"]
            == "MD5 is a a weak hash which is known to have collision. Use a strong hashing function."
        )


def test_nodejsscan_convert_metrics():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "nodejsscan",
            [],
            ".",
            {
                "total_count": {"good": 0, "mis": 8, "sec": 4},
                "vuln_count": {
                    "Loading of untrusted YAML can cause Remote Code Injection": 1,
                    "Weak Hash used - MD5": 1,
                    "XSS - Reflected Cross Site Scripting": 2,
                },
            },
            {},
            [],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert jsondata["runs"][0]["properties"]["metrics"]


def test_create_result():
    issue = issueLib.issue_from_dict(
        {
            "description": "MD5 is a a weak hash which is known to have collision. Use a strong hashing function.",
            "filename": "InsufficientPasswordHash.js",
            "line": 3,
            "lines": 'function hashPassword(password) {\n    var crypto = require("crypto");\n    var hasher = crypto.createHash(\'md5\');\n    var hashed = hasher.update(password).digest("hex"); // BAD\n    return hashed;\n}',
            "path": "/app/src/CWE-916/examples/InsufficientPasswordHash.js",
            "sha2": "bfc3a2dfec54a8e77e41c3e3d7a6d87477ea1ed6d1cb3b1b60b8e135b0d18368",
            "tag": "node",
            "title": "Weak Hash used - MD5",
        }
    )
    data = convertLib.create_result("nodetest", issue, {}, {}, None, "/app/src")
    assert (
        data.locations[0].physical_location.artifact_location.uri
        == "file:///app/src/CWE-916/examples/InsufficientPasswordHash.js"
    )
    # Override the workspace and check the location
    os.environ["WORKSPACE"] = "/foo/bar"
    importlib.reload(convertLib)
    data = convertLib.create_result("nodetest", issue, {}, {}, None, "/app/src")
    assert (
        data.locations[0].physical_location.artifact_location.uri
        == "file:///foo/bar/CWE-916/examples/InsufficientPasswordHash.js"
    )
    # Override the workspace and check the location
    os.environ["WORKSPACE"] = "https://github.com/ShiftLeftSecurity/cdxgen/blob/master"
    importlib.reload(convertLib)
    data = convertLib.create_result("nodetest", issue, {}, {}, None, "/app/src")
    assert (
        data.locations[0].physical_location.artifact_location.uri
        == "https://github.com/ShiftLeftSecurity/cdxgen/blob/master/CWE-916/examples/InsufficientPasswordHash.js"
    )


def test_create_result_relative():
    os.environ["WORKSPACE"] = ""
    importlib.reload(convertLib)
    issue = issueLib.issue_from_dict(
        {
            "line": "VERY_REDACTED ",
            "offender": "REDACTED",
            "commit": "06fd7b1f844f88fb7821df498ce6d209cb9ad875",
            "repo": "app",
            "rule": "Generic Credential",
            "commitMessage": "Add secret\n",
            "author": "Team ShiftLeft",
            "email": "hello@shiftleft.io",
            "file": "src/main/README-new.md",
            "date": "2020-01-12T19:45:43Z",
            "tags": "key, API, generic",
        }
    )
    data = convertLib.create_result("gitleaks", issue, {}, {}, None, "/app")
    assert (
        data.locations[0].physical_location.artifact_location.uri
        == "src/main/README-new.md"
    )


def test_credscan_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "credscan",
            [],
            ".",
            {},
            {},
            [
                {
                    "line": "VERY_SECRET_TOO = 'f6CGV4aMM9zedoh3OUNbSakBymo7yplB' ",
                    "offender": "SECRET_TOO = 'f6CGV4aMM9zedoh3OUNbSakBymo7yplB'",
                    "commit": "f5cf9d795d00ac5540f3ba26a1d98d9bc9c4bbbc",
                    "repo": "app",
                    "rule": "Generic Credential",
                    "commitMessage": "password\n",
                    "author": "Prabhu Subramanian",
                    "email": "guest@ngcloud.io",
                    "file": "README.md",
                    "date": "2020-01-02T21:02:40Z",
                    "tags": "key, API, generic",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert jsondata["runs"][0]["results"][0]["message"]["text"]
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "high": 1,
            "total": 1,
            "critical": 0,
            "medium": 0,
            "low": 0,
        }


def test_credscan_convert_unc():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "credscan",
            [],
            ".",
            {},
            {},
            [
                {
                    "line": "\naws_access_key_id='AKIAIO5FODNN7EXAMPLE'",
                    "offender": "AKIAIO5FODNN7EXAMPLE",
                    "commit": "0000000000000000000000000000000000000000",
                    "repo": "app",
                    "rule": "AWS Manager ID",
                    "commitMessage": "***STAGED CHANGES***",
                    "author": "",
                    "email": "",
                    "file": "/Users/prabhu/work/ShiftLeft/HelloShiftLeft/README.md",
                    "date": "1970-01-01T00:00:00Z",
                    "tags": "key, AWS",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert jsondata["runs"][0]["results"][0]["message"]["text"]
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "high": 1,
            "total": 1,
            "critical": 0,
            "medium": 0,
            "low": 0,
        }


def test_gosec_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "gosec",
            [],
            ".",
            {},
            {},
            [
                {
                    "severity": "MEDIUM",
                    "confidence": "HIGH",
                    "rule_id": "G104",
                    "details": "Errors unhandled.",
                    "file": "/app/lib/plugins/capture/capture.go",
                    "code": "io.Copy(reqbody, cwc.r.Request.Body)",
                    "line": "57",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert jsondata["runs"][0]["results"][0]["message"]["text"]
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "medium": 1,
            "total": 1,
            "critical": 0,
            "high": 0,
            "low": 0,
        }
        assert jsondata["runs"][0]["results"][0]["partialFingerprints"] == {}


def test_tfsec_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "tfsec",
            [],
            ".",
            {},
            {},
            [
                {
                    "rule_id": "AWSTEST",
                    "link": "https://github.com/liamg/tfsec/wiki/AWS018",
                    "location": {
                        "filename": "/app/main.tf",
                        "start_line": 1,
                        "end_line": 4,
                    },
                    "description": "Resource 'aws_security_group_rule.my-rule' should include a description for auditing purposes.",
                    "severity": "ERROR",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert (
            jsondata["runs"][0]["results"][0]["message"]["text"]
            == "Resource 'aws_security_group_rule.my-rule' should include a description for auditing purposes."
        )
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "critical": 1,
            "total": 1,
            "high": 0,
            "medium": 0,
            "low": 0,
        }


def test_checkov_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "checkov",
            [],
            ".",
            {},
            {},
            [
                {
                    "check_id": "CKV_AWS_20",
                    "check_name": "S3 Bucket has an ACL defined which allows public READ access.",
                    "check_result": {"result": "FAILED"},
                    "code_block": [
                        [1, 'resource "aws_s3_bucket" "data" {\n'],
                        [2, "  # bucket is public\n"],
                        [3, "  # bucket is not encrypted\n"],
                        [4, "  # bucket does not have access logs\n"],
                        [5, "  # bucket does not have versioning\n"],
                        [
                            6,
                            '  bucket        = "${local.resource_prefix.value}-data"\n',
                        ],
                        [7, '  acl           = "public-read"\n'],
                        [8, "  force_destroy = true\n"],
                        [9, "  tags = {\n"],
                        [
                            10,
                            '    Name        = "${local.resource_prefix.value}-data"\n',
                        ],
                        [11, "    Environment = local.resource_prefix.value\n"],
                        [12, "  }\n"],
                        [13, "}\n"],
                    ],
                    "file_path": "/terraform/s3.tf",
                    "file_line_range": [1, 13],
                    "resource": "aws_s3_bucket.data",
                    "evaluations": "",
                    "check_class": "checkov.terraform.checks.resource.aws.S3PublicACLRead",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert (
            jsondata["runs"][0]["results"][0]["message"]["text"]
            == "S3 Bucket has an ACL defined which allows public READ access."
        )
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "critical": 0,
            "total": 1,
            "high": 1,
            "medium": 0,
            "low": 0,
        }


def test_staticcheck_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "staticcheck",
            [],
            ".",
            {},
            {},
            [
                {
                    "code": "ST1005",
                    "severity": "error",
                    "location": {
                        "file": "/Users/guest/go/kube-score/cmd/kube-score/main.go",
                        "line": 156,
                        "column": 10,
                    },
                    "end": {
                        "file": "/Users/guest/go/kube-score/cmd/kube-score/main.go",
                        "line": 156,
                        "column": 86,
                    },
                    "message": "error strings should not be capitalized",
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert (
            jsondata["runs"][0]["results"][0]["message"]["text"]
            == "error strings should not be capitalized."
        )
        assert jsondata["runs"][0]["properties"]["metrics"] == {
            "critical": 0,
            "total": 1,
            "high": 0,
            "medium": 1,
            "low": 0,
        }
        assert jsondata["runs"][0]["results"][0]["partialFingerprints"] == {}


def test_to_uri():
    p = convertLib.to_uri("https://github.com/shiftleft/sast-scan")
    assert p == "https://github.com/shiftleft/sast-scan"
    p = convertLib.to_uri("README.md")
    assert p == "README.md"
    p = convertLib.to_uri("/home/prabhu/work/README.md")
    assert p == "file:///home/prabhu/work/README.md"
    p = convertLib.to_uri("c:\\users\\prabhu\\work\\README.md")
    assert p == "file:///c:/users/prabhu/work/README.md"
    p = convertLib.to_uri("c:\\users\\prabhu\\work/com/src/main/README.md")
    assert p == "file:///c:/users/prabhu/work/com/src/main/README.md"


def test_inspect_convert_issue():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as cfile:
        data = convertLib.report(
            "inspect",
            [],
            ".",
            {},
            {},
            [
                {
                    "applicationId": "HelloShiftLeft",
                    "vulnerability": {
                        "firstDetected": "1587134045",
                        "vulnerabilityId": "command-injection-attacker-controlled/b9790fedb5c49bf0c10a7cf72b0a5eab",
                        "category": "a1-injection",
                        "title": "Remote Code Execution: Command Injection through attacker-controlled data via `foo` in `SearchController.doGetSearch`",
                        "description": "Attacker controlled data is used in a shell command without undergoing escaping or validation. This could allow an attacker to execute code on the server. Injection flaws occur when untrusted data is sent to an interpreter as part of a command or query. By injecting hostile data, an attacker may trick the interpreter into executing unintended commands or accessing data without authorization which can result in data loss, corruption, or disclosure to unauthorized parties, loss of accountability, denial of access or even a complete host takeover.\n\n\n## Countermeasures\n\nThis vulnerability can be prevented by using parameterized queries or by validating HTTP data (preferably on server-side by means of common input sanitation libraries or whitelisting) before using it.\n\n## Additional information\n\n**[CWE-77](https://cwe.mitre.org/data/definitions/77.html)**\n\n**[CWE-78](https://cwe.mitre.org/data/definitions/78.html)**\n\n**[CWE-917](https://cwe.mitre.org/data/definitions/917.html)**\n\n**[OWASP-A1](https://owasp.org/www-project-top-ten/OWASP_Top_Ten_2017/Top_10-2017_A1-Injection)**",
                        "score": 9,
                        "severity": "SEVERITY_HIGH_IMPACT",
                        "dataFlow": {
                            "spId": "sl/49089d37-68ff-47e3-9035-269e6e91a44d/HelloShiftLeft/86ad7190555ddb774563ac58d242919db87a0265/56f81248989870704c18042cc58d9ff18573e7aff5f1a8cb2a92f022556a20be/1",
                            "occurrenceHash": "b9790fedb5c49bf0c10a7cf72b0a5eab",
                            "dataFlow": {
                                "list": [
                                    {
                                        "location": {
                                            "lineNumber": 21,
                                            "packageName": "io.shiftleft.controller",
                                            "className": "io.shiftleft.controller.SearchController",
                                            "methodName": "io.shiftleft.controller.SearchController.doGetSearch:java.lang.String(java.lang.String,javax.servlet.http.HttpServletResponse,javax.servlet.http.HttpServletRequest)",
                                            "shortMethodName": "doGetSearch",
                                            "fileName": "io/shiftleft/controller/SearchController.java",
                                        },
                                        "variableInfo": {
                                            "parameter": {
                                                "symbol": "foo",
                                                "paramIndex": 1,
                                                "type": "java.lang.String",
                                            }
                                        },
                                        "methodId": "6974698689270346897",
                                        "parameterId": "6974698689270346900",
                                        "methodTags": [
                                            {"key": "INTERFACE_WRITE"},
                                            {"key": "EXPOSED_METHOD"},
                                            {"key": "INTERFACE_READ"},
                                            {
                                                "key": "EXPOSED_METHOD_ROUTE",
                                                "value": "/search/user",
                                            },
                                        ],
                                        "parameterTags": [
                                            {"key": "FROM_OUTSIDE", "value": "http"},
                                            {
                                                "key": "DATA_TYPE",
                                                "value": "attacker-controlled",
                                            },
                                        ],
                                        "id": "6974698689270346900",
                                    },
                                    {
                                        "location": {
                                            "lineNumber": 25,
                                            "packageName": "io.shiftleft.controller",
                                            "className": "io.shiftleft.controller.SearchController",
                                            "methodName": "io.shiftleft.controller.SearchController.doGetSearch:java.lang.String(java.lang.String,javax.servlet.http.HttpServletResponse,javax.servlet.http.HttpServletRequest)",
                                            "shortMethodName": "doGetSearch",
                                            "fileName": "io/shiftleft/controller/SearchController.java",
                                        },
                                        "variableInfo": {
                                            "local": {
                                                "symbol": "foo",
                                                "type": "java.lang.String",
                                            }
                                        },
                                        "methodId": "6974698689270346897",
                                        "methodTags": [
                                            {"key": "INTERFACE_WRITE"},
                                            {"key": "EXPOSED_METHOD"},
                                            {"key": "INTERFACE_READ"},
                                            {
                                                "key": "EXPOSED_METHOD_ROUTE",
                                                "value": "/search/user",
                                            },
                                        ],
                                        "id": "6974698689270346957",
                                    },
                                    {
                                        "location": {
                                            "packageName": "org.springframework.expression.spel.standard",
                                            "className": "org.springframework.expression.spel.standard.SpelExpressionParser",
                                            "methodName": "org.springframework.expression.spel.standard.SpelExpressionParser.parseExpression:org.springframework.expression.Expression(java.lang.String)",
                                            "shortMethodName": "parseExpression",
                                            "fileName": "org/springframework/expression/spel/standard/SpelExpressionParser.java",
                                        },
                                        "variableInfo": {
                                            "parameter": {
                                                "symbol": "param0",
                                                "paramIndex": 1,
                                                "type": "java.lang.String",
                                            }
                                        },
                                        "methodId": "2545",
                                        "parameterId": "2548",
                                        "methodTags": [
                                            {"key": "INTERFACE_READ"},
                                            {"key": "INTERFACE_WRITE"},
                                        ],
                                        "parameterTags": [
                                            {"key": "TO_OUTSIDE", "value": "execute"},
                                            {
                                                "key": "DESCRIPTOR_USE",
                                                "value": "execute",
                                            },
                                        ],
                                        "id": "2548",
                                    },
                                ]
                            },
                        },
                        "firstVersionDetected": "86ad7190555ddb774563ac58d242919db87a0265",
                    },
                }
            ],
            cfile.name,
        )
        jsondata = json.loads(data)
        assert jsondata


def test_inspect_extract_issue():
    issues, metrics, skips = convertLib.extract_from_file(
        "inspect",
        Path(__file__).parent,
        Path(__file__).parent / "data" / "inspect-report.json",
    )
    assert issues
    assert len(issues) == 99
    assert issues[0] == {
        "rule_id": "a1-injection",
        "title": "Remote Code Execution: Command Injection through attacker-controlled data via `foo` in `SearchController.doGetSearch`",
        "description": "Attacker controlled data is used in a shell command without undergoing escaping or validation. This could allow an attacker to execute code on the server. Injection flaws occur when untrusted data is sent to an interpreter as part of a command or query. By injecting hostile data, an attacker may trick the interpreter into executing unintended commands or accessing data without authorization which can result in data loss, corruption, or disclosure to unauthorized parties, loss of accountability, denial of access or even a complete host takeover.\n\n\n## Countermeasures\n\nThis vulnerability can be prevented by using parameterized queries or by validating HTTP data (preferably on server-side by means of common input sanitation libraries or whitelisting) before using it.\n\n## Additional information\n\n**[CWE-77](https://cwe.mitre.org/data/definitions/77.html)**\n\n**[CWE-78](https://cwe.mitre.org/data/definitions/78.html)**\n\n**[CWE-917](https://cwe.mitre.org/data/definitions/917.html)**\n\n**[OWASP-A1](https://owasp.org/www-project-top-ten/OWASP_Top_Ten_2017/Top_10-2017_A1-Injection)**",
        "score": 9,
        "severity": "SEVERITY_HIGH_IMPACT",
        "line_number": 21,
        "filename": "io/shiftleft/controller/SearchController.java",
        "first_found": "86ad7190555ddb774563ac58d242919db87a0265",
        "issue_confidence": "HIGH",
    }
