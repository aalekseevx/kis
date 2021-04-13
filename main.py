import json
from typing import Dict, List, Set
from dataclasses import dataclass
from cachetools import cached
from cachetools.keys import hashkey
import sys


@dataclass()
class KisTable:
    """
    Table with the courses of the KIS department
    """
    courses: Dict
    min_courses_per_semester: int
    chosen_courses: Set
    courses_by_semesters: List
    predefined_priority: int

    @cached(cache={}, key=lambda course, query: hashkey(query))
    def get_course_score(self, course):
        """
        Get course score. Score is pair of integers, representing the number of
        required dependencies in the dependency tree
        """
        score = (-1, self.courses[course]['priority'])
        for dep in self.courses[course]['deps']:
            if isinstance(dep, str):
                score = [sum(x) for x in
                         zip(score, self.get_course_score(dep))]
            else:
                score = [sum(x) for x in zip(
                    score, max([self.get_course_score(x) for x in dep])
                )]
        return score

    def remove_variative_deps(self):
        """
        Removes variative dependencies - prefer courses with higher score as
        a dependency
        """
        for course in self.courses:
            for dep in self.courses[course]['deps']:
                ans = set()
                if isinstance(dep, list):
                    ans.add(max(
                        zip(map(self.get_course_score, dep), dep)
                    )[1])
                else:
                    ans.add(dep)
                self.courses[course]['deps'] = ans

    def make_closure(self):
        """
        Some courses are already chosen, so let's add all there dependencies
        Use only when variational deps are removed
        """
        is_closed = False
        while not is_closed:
            is_closed = True
            to_add = set()
            for course in self.chosen_courses:
                for dep in self.courses[course]['deps']:
                    if dep not in self.chosen_courses:
                        to_add.add(dep)
                        is_closed = False
            for item in to_add:
                self.chosen_courses.add(item)

        self.predefined_priority = sum(
            map(
                lambda x: self.courses[x]['priority'],
                self.chosen_courses)
        )

        # Remove chosen courses out of list and dependencies
        for course in self.chosen_courses:
            del self.courses[course]
        for course in self.chosen_courses:
            for course_reverse_dep in self.courses:
                if course in self.courses[course_reverse_dep]['deps']:
                    del self.courses[course_reverse_dep]['deps'][course]

    def add_until_full(self):
        courses_left = max(0, self.min_courses_per_semester * 7 - len(
            self.chosen_courses))
        # Add ones with the highest score
        self.chosen_courses.add(
            *sorted(
                self.courses.items(),
                key=lambda x: self.get_course_score(x),
                reverse=True)[:courses_left]
        )


def main():
    with open(sys.argv[1]) as fin:
        raw_data = json.load(fin)
    data = KisTable(courses=raw_data['courses'],
                    min_courses_per_semester=int(
                        raw_data['min_courses_per_semester']),
                    chosen_courses=set(raw_data['chosen_courses']),
                    courses_by_semesters=[0, 0, 0, 0, 0, 0],
                    predefined_priority=0)
    data.remove_variative_deps()
    data.make_closure()
    data.add_until_full()
    print("Result:")
    print(data.chosen_courses)


if __name__ == '__main__':
    main()
