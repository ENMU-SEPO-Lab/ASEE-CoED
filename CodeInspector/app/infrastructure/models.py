from dataclasses import dataclass, field
from typing import TypeAlias, ClassVar
from collections import Counter
from collections.abc import Iterable

@dataclass
class CheckstyleViolation:
    file_name: str
    line: int
    severity: str
    type_name: str
    message: str
    category: str | None = None
    
@dataclass
class PmdViolation:
    file_name: str
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
    summary: UnitTestingSummary | None = None
    testcases: list[UnitTestCase] | None = None
    test_suite: str | None = None
    
@dataclass
class CombinedParsedViolations:
    checkstyle: list[CheckstyleViolation]
    pmd: list[PmdViolation]
    unit_testing: UnitTestingResults

def aggregate_counters(counters: Iterable[Counter]) -> Counter:
    """aggregate multiple Counter objects into one.

    Args:
        counters (Iterable[Counter]): iterable object containing counters

    Returns:
        Counter: the counter containing the result of the aggregation
    """
    total = Counter()
    for counter in counters:
        total += counter
    return total

# a violation can be either of type Checkstyle or PMD
Violation: TypeAlias = CheckstyleViolation | PmdViolation

@dataclass
class ViolationsWithinType:
    # each error type can occur multiple times
    violations: list[Violation] = field(default_factory=list)
    
    def get_error_count_in_type(self) -> int:
        """Gets the total error count within type"""
        return len(self.violations)
        
@dataclass
class TypesWithinCategory:
    # one category class can have multiple subtypes
    # type_name: str -> type_structure
    types: dict[str, ViolationsWithinType] = field(default_factory=dict)
     
    def get_type_counts_in_cat(self) -> Counter:
        """Gets the number of errors of each type within a category.

        Returns:
            Counter: items of form (type_name: str -> error_count: int)
        """
        counts = Counter({
            type_name: type_data.get_error_count_in_type() 
            for type_name, type_data in self.types.items()
        })
        
        return counts
    
    def get_error_count_in_cat(self) -> int:
        """Gets the total error count within category"""
        return self.get_type_counts_in_cat().total()
    
    def get_top_n_types_and_counts_in_cat(self, top_n: int) -> list[tuple[str, int]]:
        """Gets the top_n error types by count within a category

        Args:
            top_n (int): the desired top_n number (how many elements the return list should have)

        Returns:
            list[tuple[str, int]]: list[(type_name, error_count),...] with top_n elements if that many error types exist
        """
        return self.get_type_counts_in_cat().most_common(top_n)
    
@dataclass
class CategoriesWithinSeverity:
    # one severity class can have multiple subcategories.
    # category_name: str -> category_structure 
    categories: dict[str, TypesWithinCategory] = field(default_factory=dict)
    
    def get_cat_counts_in_sev(self) -> Counter:
        """Gets the number of errors of each category within a severity

        Returns:
            Counter: items of form (cat_name: str -> error_count: int)
        """
        counts = Counter({
            cat_name: cat_data.get_error_count_in_cat()
            for cat_name, cat_data in self.categories.items()
        })
        
        return counts
    
    def get_type_counts_in_sev(self) -> Counter:
        """Gets the number of errors of each type within a severity.

        Returns:
            Counter: items of form (type_name: str -> error_count: int)
        """
        return aggregate_counters(
            cat.get_type_counts_in_cat()
            for cat in self.categories.values()
        )
        
    def get_error_count_in_sev(self) -> int:
        """Gets the total error count within severity"""
        return self.get_cat_counts_in_sev().total()
    
    def get_top_n_error_types_and_counts_in_sev(self, top_n: int) -> list[tuple[str, int]]:
        """Gets the top_n error types by count within a severity

        Args:
            top_n (int): the desired top_n number (how many elements the return list should have)

        Returns:
            list[tuple[str, int]]: list[(type_name, type_count),...] with top_n elements if that many error types exist
        """
        return self.get_type_counts_in_sev().most_common(top_n)
    
@dataclass
class SeveritiesWithinFile:
    SEV_TEMPLATE: ClassVar[dict[str, type[CategoriesWithinSeverity]]] = {}
    
    # one file can contain errors of multiple severity classes (checkstyle: 3, pmd: 5)
    # severity_name: str -> severity_structure 
    severities: dict[str, CategoriesWithinSeverity] = field(init=False)
    
    def __post_init__(self):
        self.severities = {key: cls() for key, cls in self.SEV_TEMPLATE.items()}
        
    def get_type_counts_per_severity_in_file(self) -> dict[str, Counter]:
        """gets the error type counts of every type encountered, within each severity of the file

        Returns:
            dict[str, Counter]: (severity_name: str, Counter[type_name: str, error_count: int])
        """
        type_counts_in_severities = {}
        
        for severity in self.SEV_TEMPLATE.keys():
            type_counts_in_severities[severity] = self.severities[severity].get_type_counts_in_sev()
        
        return type_counts_in_severities
    
    def get_sev_counts_in_file(self) -> Counter:
        """Gets the number of errors of each severit within a file

        Returns:
            Counter: items of form (sev_name: str -> error_count: int)
        """
        counts = Counter({
            sev_name: sev_data.get_error_count_in_sev()
            for sev_name, sev_data in self.severities.items()
        })
        
        return counts
    
    def get_type_counts_in_file(self) -> Counter:
        """Gets the number of errors of each type within a file.

        Returns:
            Counter: items of form (type_name: str -> error_count: int)
        """
        return aggregate_counters(
            sev.get_type_counts_in_sev()
            for sev in self.severities.values()
        )
    
    def get_error_count_in_file(self) -> int:
        """Gets the total error count within file"""
        return self.get_sev_counts_in_file().total()
    
    def get_top_n_error_types_and_counts_in_file(self, top_n: int) -> list[tuple[str, int]]:
        """Gets the top_n error types by count within a file

        Args:
            top_n (int): the desired top_n number (how many elements the return list should have)

        Returns:
            list[tuple[str, int]]: list[(type_name, type_count),...] with top_n elements if that many error types exist
        """
        return self.get_type_counts_in_file().most_common(top_n)

@dataclass
class CheckstyleSeveritiesWithinFile(SeveritiesWithinFile):
    
    SEV_TEMPLATE = {
        "info": CategoriesWithinSeverity,
        "warning": CategoriesWithinSeverity,
        "error": CategoriesWithinSeverity
    }

@dataclass
class PmdSeveritiesWithinFile(SeveritiesWithinFile):
    
    SEV_TEMPLATE = {
        "5": CategoriesWithinSeverity,
        "4": CategoriesWithinSeverity,
        "3": CategoriesWithinSeverity,
        "2": CategoriesWithinSeverity,
        "1": CategoriesWithinSeverity
    }
    
def severity_key_count(cls: type[SeveritiesWithinFile]) -> int:
    """Gets the specific number of severities for a given SeveritiesWithinFile class

    Args:
        cls (type[SeveritiesWithinFile]): the specific class

    Returns:
        int: the number of severities associated with the class
    """
    return len(cls.SEV_TEMPLATE)
# file -> severity -> category -> type -> count
@dataclass
class ProcessedViolations:
    # one submission can contain multiple files.
    # file_name -> file_datastructure
    severity_class: type[SeveritiesWithinFile] # CheckstyleSeveritiesWithinFile or PmdSeveritiesWithinFile
    files: dict[str, SeveritiesWithinFile] = field(default_factory=dict)
        
    def get_type_counts_in_submission(self) -> Counter:
        """Gets the number of errors of each type within a submission.

        Returns:
            Counter: items of form (type_name: str -> error_count: int)
        """
        return aggregate_counters(
            file.get_type_counts_in_file()
            for file in self.files.values()
        )
        
    def get_type_counts_per_severity_in_submission(self) -> dict[str, Counter]:
        """gets the error type counts of every type encountered, within each severity of the submission

        Returns:
            dict[str, Counter]: (severity_name: str, Counter[type_name: str, error_count: int])
        """
        counts_in_submission = {sev: Counter() for sev in self.severity_class.SEV_TEMPLATE.keys()}
        
        for file_data in self.files.values():
            counts_in_single_file = file_data.get_type_counts_per_severity_in_file()
            for sev, sev_counter in counts_in_single_file.items():
                counts_in_submission[sev] += sev_counter
        
        return counts_in_submission
    
    def get_file_counts_in_submission(self) -> Counter:
        """Gets the number of errors in each file within the submission

        Returns:
            Counter: items of form (file_name: str -> error_count: int)
        """
        counts = Counter({
            file_name: file_data.get_error_count_in_file()
            for file_name, file_data in self.files.items()
        })
        
        return counts
    
    def get_error_count_within_submission(self) -> int:
        """Gets the total error count within submission"""
        return self.get_file_counts_in_submission().total()
    
    def get_severity_counts(self) -> Counter:
        """Gets the number of errors within each severity class across the submission

        Returns:
            Counter: items of form (sev_name: str -> error_count: int)
        """
        counts = Counter({
            severity_name: 0 
            for severity_name in self.severity_class.SEV_TEMPLATE.keys()
        })
        
        for file_data in self.files.values():
            for sev_name, sev_data in file_data.severities.items():
                counts[sev_name] += sev_data.get_error_count_in_sev()
        
        return counts
                
    def get_severity_ratios(self) -> list[float]:
        """Gets the ratio in % of each severity class relative to the total error count 

        Returns:
            list[float]: index 0 is the ratio of the lowest sev class, last one is the highest
            if total doesn't exist, the ratio defaults to 0%
        """
        counts = self.get_severity_counts()
        total = counts.total()
        return {
            sev: (counts[sev] / total * 100.0) if total else 0.0 
            for sev in self.severity_class.SEV_TEMPLATE.keys()
        }
    
    def get_top_n_error_types_and_counts_in_subm(self, top_n: int) -> list[tuple[str, int]]:
        """Gets the top_n error types by count within a submission

        Args:
            top_n (int): the desired top_n number (how many elements the return list should have)

        Returns:
            list[tuple[str, int]]: list[(type_name, type_count),...] with top_n elements if that many error types exist
        """
        return self.get_type_counts_in_submission().most_common(top_n)
        
    def file_bucket(self, file_name: str) -> SeveritiesWithinFile:
        return self.files.setdefault(file_name, self.severity_class())
    
    def add_violation(
        self, 
        file_name: str, 
        severity: str, 
        category: str, 
        type_name: str, 
        violation: Violation
    ) -> None:
        file_bucket = self.file_bucket(file_name)
        severity_bucket = file_bucket.severities.setdefault(severity, CategoriesWithinSeverity())
        category_bucket = severity_bucket.categories.setdefault(category, TypesWithinCategory())
        type_bucket = category_bucket.types.setdefault(type_name, ViolationsWithinType())
        type_bucket.violations.append(violation)

@dataclass
class ProcessedJunitTests:
    all_tests: list[UnitTestCase]
    failed_tests: list[UnitTestCase]
    
    """
    
    -file_name
        |
        "info"
            |
            cat_1
                |
                type_1 -> # of occurrences
                |
                type_2 -> # of occurrences
            |   
            cat_2
        |
        "warning"
        |
        "error"
    
    
    """

@dataclass 
class ProcessedSubmission:
    cs_processed: ProcessedViolations
    pmd_processed: ProcessedViolations
    junit_processed: ProcessedJunitTests

@dataclass
class SubmissionData:
    date: str
    upload_dir_name: str
    email: str
    loc: int
    cs_score: int
    cs_weighted_error: float
    cs_violation_count: int
    cs_sev_counts: Counter
    pmd_score: int
    pmd_weighted_error: float
    pmd_violation_count: int
    pmd_sev_counts: Counter
    junit_test_count: int
    junit_failed_count: int
    coding_std_score: int
    req_score: int
    overall_score: int
    overall_weighted_error: float
    top_cs_error_types: list[tuple[str, int]]
    top_pmd_error_types: list[tuple[str, int]]
    run_score: int | None = None
