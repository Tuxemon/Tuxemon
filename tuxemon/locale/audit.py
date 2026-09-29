# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.locale.finder import LocaleFinder

logger = logging.getLogger(__name__)


class LocaleAudit:
    """
    Provides analytical tools for inspecting and reporting on translation
    coverage discovered by LocaleFinder.
    """

    def __init__(self, finder: LocaleFinder) -> None:
        self.finder = finder

    def count_domains_per_locale(self) -> dict[str, int]:
        """
        Returns a mapping of each locale to the number of unique domains
        (.po files) it contains.
        """
        domain_count: dict[str, int] = defaultdict(int)
        for info in self.finder.search_locales():
            domain_count[info.locale] += 1
        return dict(domain_count)

    def find_locales_missing_domain(self, required_domain: str) -> list[str]:
        """
        Identifies which locales are missing a required domain.
        """
        domain_map = defaultdict(set)
        for info in self.finder.search_locales():
            domain_map[info.locale].add(info.domain)
        return [
            locale
            for locale, domains in domain_map.items()
            if required_domain not in domains
        ]

    def locale_category_matrix(self) -> dict[str, set[str]]:
        """
        Constructs a mapping of locales to the set of categories they contain.
        Useful for visualizing cross-category coverage.
        """
        matrix = defaultdict(set)
        for info in self.finder.search_locales():
            matrix[info.locale].add(info.category)
        return dict(matrix)

    def validate_locale(self, locale: str, required_domains: set[str]) -> bool:
        """
        Checks whether the given locale includes all required domains.
        Logs any missing domains and returns False if any are missing.
        """
        found = {
            info.domain
            for info in self.finder.search_locales()
            if info.locale == locale
        }
        missing = required_domains - found
        if missing:
            logger.warning(
                f"Locale '{locale}' is missing required domains: {missing}"
            )
            return False
        return True

    def report_summary(self) -> None:
        """
        Logs an audit summary report of discovered locales and their domain
        counts.
        """
        summary = self.count_domains_per_locale()
        logger.info("Locale Audit Summary:")
        for locale, count in sorted(summary.items()):
            logger.info(f"  {locale}: {count} domains")

    def get_incomplete_locales(self, required_domains: set[str]) -> list[str]:
        """
        Returns a list of locales that are missing one or more required
        domains.
        """
        incomplete = []
        for locale in self.finder.get_locale_names():
            if not self.validate_locale(locale, required_domains):
                incomplete.append(locale)
        return incomplete
