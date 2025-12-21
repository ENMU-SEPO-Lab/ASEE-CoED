from dataclasses import dataclass, field
from typing import TypeAlias

@dataclass
class CheckstyleViolation:
    file: str
    line: int
    severity: str
    message: str
    source: str
    
@dataclass
class PmdViolation:
    file: str
    begin_line: int
    end_line: int
    begin_column: int
    end_column: int
    rule: str
    ruleset: str
    priority: int
    message: str
    class_name: str | None = None
    external_info_url: str | None = None
    method: str | None = None
    variable: str | None = None

@dataclass
class TestFailureDetails:
    message: str = ""
    stack_trace: list[str] = field(default_factory=list)
    
@dataclass
class UnitTestingSummary:
    tests_ran: int = 0
    failures: int = 0 
    errors: int = 0
    skipped: int = 0
    time_elapsed: str = ""
 
@dataclass 
class UnitTestCase:
    name: str | None = None
    time: str | None = None
    status: str | None = None  
    failure_details: TestFailureDetails | None = None
    
@dataclass 
class UnitTestingResults:
    summary: UnitTestingSummary
    testcases: list[UnitTestCase]
    test_suite: str | None = None
    
@dataclass
class CombinedParsedViolations:
    checkstyle: list[CheckstyleViolation]
    pmd: list[PmdViolation]
    unit_testing: UnitTestingResults 
    
@dataclass
class ViolationReport:
    system: str
    student_name: str
    check_date: str
    lines_of_code: int
    violations: CombinedParsedViolations

# a violation can be either of type Checkstyle or PMD
Violation: TypeAlias = CheckstyleViolation | PmdViolation

@dataclass
class ErrorsWithinType:
    # each error type can occur multiple times
    violations: list[Violation] = field(default_factory=list)
    
    def total_errors(self) -> int:
        # get total error count within type
        return len(self.violations)
        
@dataclass
class TypesWithinCategory:
    # one category class can have multiple subtypes
    # type_name: str -> type_structure
    types: dict[str, ErrorsWithinType] = field(default_factory=dict)
    
    def total_errors(self) -> int:
        # get total error count within category
        return sum(
            type.total_errors()
            for type in self.types.values()
        )
    
    def get_most_common_error_type_and_count(self) -> tuple[str, int]:
        
        if not self.types:
            return ("None", 0) 
        
        return max(
                (
                    (type_name, type_class.total_errors())
                    for type_name, type_class in self.types.items()
                ),
                key=lambda type_and_count: type_and_count[1]
            )  
    
@dataclass
class CategoriesWithinSeverity:
    # one severity class can have multiple subcategories.
    # category_name: str -> category_structure 
    
    categories: dict[str, TypesWithinCategory] = field(default_factory=dict)
    
    def total_errors(self) -> int:
        # get total error count within severity
        return sum(
            category.total_errors()
            for category in self.categories.values()
        )
        
    def get_most_common_error_category_and_count(self) -> tuple[str, int]:
        
        if not self.categories:
            return ("None", 0) 
        
        return max(
                (
                    (category_name, category_class.total_errors())
                    for category_name, category_class in self.categories.items()
                ),
                key=lambda category_and_count: category_and_count[1]
            )   
    
@dataclass
class SeveritiesWithinFile:
    # one file can contain errors of multiple severity classes (checkstyle: 3, pmd: 5)
    # severity_name: str -> severity_structure 
    severities: dict[str, CategoriesWithinSeverity] = field(default_factory=dict)
    
    def total_errors(self) -> int:
        # get total error count within file
        return sum(
            severity.total_errors()
            for severity in self.severities.values()
        )
        
    def get_most_common_severity(self) -> tuple[str, int]:
        if not self.severities:
            return ("None", 0)

        return max(
            (
                (severity_name, severity_class.total_errors()) 
                for severity_name, severity_class in self.severities.items()
            ),
            key=lambda severity_and_count: severity_and_count[1]
        )   
    
@dataclass
class FilesWithinSubmission:
    # one submission can contain multiple files.
    # file_name -> file_datastructure
    files: dict[str, SeveritiesWithinFile] = field(default_factory=dict)
    
    def total_errors(self) -> int:
        # get total error count within submission
        return sum(
            file.total_errors()
            for file in self.files.values()
        )
        
    def get_file_with_most_errors(self) -> tuple[str, int]:
    
        if not self.files:
            return ("None", 0)

        return max(
            (
                (file_name, stats.total_errors()) 
                for file_name, stats in self.files.items()
            ),
            key=lambda file_and_count: file_and_count[1]
        )
        
    def add_violation(self, file_name: str, severity: str, category: str, type_name: str, violation: Violation) -> None:
        
        file_bucket = self.files.setdefault(file_name, SeveritiesWithinFile())
        severity_bucket = file_bucket.severities.setdefault(severity, CategoriesWithinSeverity())
        category_bucket = severity_bucket.categories.setdefault(category, TypesWithinCategory())
        type_bucket = category_bucket.types.setdefault(type_name, ErrorsWithinType())
        type_bucket.violations.append(violation)