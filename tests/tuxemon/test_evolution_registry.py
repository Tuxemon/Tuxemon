# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
import unittest
from uuid import UUID

from tuxemon.monster_dir.evolution_registry import EvolutionRegistry


class TestEvolutionRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = EvolutionRegistry()
        logging.basicConfig(level=logging.DEBUG)
        self.monster_id = UUID("123e4567-e89b-12d3-a456-426655440000")
        self.evolution_slug = "slug"
        self.level = 1

    def test_log_missed(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.assertEqual(
            len(self.registry._missed_evolutions[self.monster_id]), 1
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].slug,
            self.evolution_slug,
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].level,
            self.level,
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].count, 1
        )

    def test_log_missed_increment(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.assertEqual(
            len(self.registry._missed_evolutions[self.monster_id]), 1
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].slug,
            self.evolution_slug,
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].level,
            self.level,
        )
        self.assertEqual(
            self.registry._missed_evolutions[self.monster_id][0].count, 2
        )

    def test_get_retryable_missed(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        retryable = self.registry.get_retryable_missed(self.monster_id)
        self.assertEqual(retryable, [self.evolution_slug])

    def test_get_retryable_missed_max_attempts(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        retryable = self.registry.get_retryable_missed(
            self.monster_id, max_attempts=3
        )
        self.assertEqual(retryable, [])

    def test_clear_missed(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.registry.clear_missed(self.monster_id)
        self.assertNotIn(self.monster_id, self.registry._missed_evolutions)

    def test_add_pending(self):
        self.registry.add_pending(self.monster_id, self.evolution_slug)
        self.assertEqual(
            self.registry.get_pending(self.monster_id), [self.evolution_slug]
        )

    def test_get_pending(self):
        self.registry.add_pending(self.monster_id, self.evolution_slug)
        self.assertEqual(
            self.registry.get_pending(self.monster_id), [self.evolution_slug]
        )

    def test_clear_pending(self):
        self.registry.add_pending(self.monster_id, self.evolution_slug)
        self.registry.clear_pending(self.monster_id)
        self.assertNotIn(self.monster_id, self.registry._pending_evolutions)

    def test_get_blocked(self):
        self.registry.block_evolution_forever(
            self.monster_id, self.evolution_slug
        )
        self.assertEqual(
            self.registry.get_blocked(self.monster_id), {self.evolution_slug}
        )

    def test_block_evolution_forever(self):
        self.registry.log_missed(self.monster_id, self.evolution_slug, 1)
        self.registry.block_evolution_forever(
            self.monster_id, self.evolution_slug
        )
        self.assertNotIn(self.monster_id, self.registry._missed_evolutions)
        self.assertNotIn(
            self.evolution_slug, self.registry.get_pending(self.monster_id)
        )
        self.assertIn(
            self.evolution_slug, self.registry.get_blocked(self.monster_id)
        )

    def test_unblock_evolution(self):
        self.registry.block_evolution_forever(
            self.monster_id, self.evolution_slug
        )
        self.registry.unblock_evolution(self.monster_id, self.evolution_slug)
        self.assertNotIn(
            self.evolution_slug, self.registry.get_blocked(self.monster_id)
        )

    def test_clear_pending_slug(self):
        self.registry.add_pending(self.monster_id, self.evolution_slug)
        self.registry.clear_pending_slug(self.monster_id, self.evolution_slug)
        self.assertEqual(self.registry.get_pending(self.monster_id), [])

    def test_encode_registry(self):
        self.registry.log_missed(
            self.monster_id, self.evolution_slug, self.level
        )
        self.registry.add_pending(self.monster_id, self.evolution_slug)
        self.registry._blocked_evolutions.setdefault(
            self.monster_id, set()
        ).add(self.evolution_slug)
        encoded_registry = self.registry.encode_registry()
        self.assertIn(self.monster_id.hex, encoded_registry["missed"])
        self.assertIn(self.monster_id.hex, encoded_registry["pending"])
        self.assertIn(self.monster_id.hex, encoded_registry["blocked"])

    def test_decode_registry(self):
        data = {
            "missed": {
                self.monster_id.hex: [
                    {
                        "slug": self.evolution_slug,
                        "level": self.level,
                        "count": 1,
                    }
                ]
            },
            "pending": {self.monster_id.hex: [self.evolution_slug]},
            "blocked": {self.monster_id.hex: [self.evolution_slug]},
        }
        self.registry.decode_registry(data)
        self.assertEqual(
            len(self.registry._missed_evolutions[self.monster_id]), 1
        )
        self.assertEqual(
            self.registry.get_pending(self.monster_id), [self.evolution_slug]
        )
        self.assertEqual(
            self.registry.get_blocked(self.monster_id), {self.evolution_slug}
        )

    def test_clear_missed_slug(self):
        slug1 = "fire"
        slug2 = "water"

        self.registry.log_missed(self.monster_id, slug1, self.level)
        self.registry.log_missed(self.monster_id, slug2, self.level)

        self.registry.clear_missed(self.monster_id, slug1)

        missed = self.registry._missed_evolutions[self.monster_id]
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0].slug, slug2)

    def test_get_retryable_mixed_counts(self):
        slug1 = "fire"
        slug2 = "water"

        for _ in range(2):
            self.registry.log_missed(self.monster_id, slug1, self.level)
        for _ in range(4):
            self.registry.log_missed(self.monster_id, slug2, self.level)

        retryable = self.registry.get_retryable_missed(
            self.monster_id, max_attempts=3
        )
        self.assertEqual(retryable, [slug1])

    def test_encode_empty_registry(self):
        encoded = self.registry.encode_registry()
        self.assertEqual(encoded["missed"], {})
        self.assertEqual(encoded["pending"], {})
        self.assertEqual(encoded["blocked"], {})

    def test_decode_registry_partial(self):

        data = {
            "missed": {
                self.monster_id.hex: [
                    {
                        "slug": self.evolution_slug,
                        "level": self.level,
                        "count": 1,
                    }
                ]
            }
            # No 'pending' or 'blocked'
        }
        self.registry.decode_registry(data)
        self.assertEqual(
            len(self.registry._missed_evolutions[self.monster_id]), 1
        )
        self.assertEqual(self.registry.get_pending(self.monster_id), [])
        self.assertEqual(self.registry.get_blocked(self.monster_id), set())

    def test_decode_registry_malformed(self):
        malformed_data = {
            "missed": {
                "not-a-uuid": [{"slug": "fire", "level": 1, "count": 1}]
            },
            "pending": {"also-not-a-uuid": ["water"]},
            "blocked": {"bad-uuid": ["earth"]},
        }

        with self.assertRaises(ValueError):
            self.registry.decode_registry(malformed_data)

    def test_log_missed_different_levels(self):
        slug = "fire"

        self.registry.log_missed(self.monster_id, slug, level=1)
        self.registry.log_missed(self.monster_id, slug, level=2)

        missed = self.registry._missed_evolutions[self.monster_id]
        self.assertEqual(len(missed), 2)
        self.assertEqual({evo.level for evo in missed}, {1, 2})

    def test_multiple_slugs_same_monster(self):
        slugs = ["fire", "water", "earth"]

        for slug in slugs:
            self.registry.log_missed(self.monster_id, slug, level=1)

        missed = self.registry._missed_evolutions[self.monster_id]
        self.assertEqual(len(missed), 3)
        self.assertEqual({evo.slug for evo in missed}, set(slugs))

    def test_registry_round_trip(self):
        slug = "fire"

        self.registry.log_missed(self.monster_id, slug, self.level)
        self.registry.add_pending(self.monster_id, slug)
        self.registry._blocked_evolutions.setdefault(
            self.monster_id, set()
        ).add(slug)

        encoded = self.registry.encode_registry()

        new_registry = EvolutionRegistry()
        new_registry.decode_registry(encoded)

        self.assertEqual(
            new_registry._missed_evolutions[self.monster_id][0].slug, slug
        )
        self.assertEqual(new_registry.get_pending(self.monster_id), [slug])
        self.assertEqual(new_registry.get_blocked(self.monster_id), {slug})

    def test_clear_missed_slug_after_decode(self):
        slug1 = "fire"
        slug2 = "water"

        # Simulate encoded data with two missed evolutions
        data = {
            "missed": {
                self.monster_id.hex: [
                    {"slug": slug1, "level": self.level, "count": 1},
                    {"slug": slug2, "level": self.level, "count": 1},
                ]
            }
        }

        self.registry.decode_registry(data)
        self.registry.clear_missed(self.monster_id, slug1)

        missed = self.registry._missed_evolutions.get(self.monster_id, [])
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0].slug, slug2)

    def test_clear_pending_slug_after_decode(self):
        slug1 = "fire"
        slug2 = "water"

        data = {"pending": {self.monster_id.hex: [slug1, slug2]}}

        self.registry.decode_registry(data)
        self.registry.clear_pending_slug(self.monster_id, slug1)

        pending = self.registry.get_pending(self.monster_id)
        self.assertEqual(pending, [slug2])

    def test_clear_missed_nonexistent_slug(self):
        slug = "fire"

        self.registry.log_missed(self.monster_id, slug, self.level)
        self.registry.clear_missed(self.monster_id, "nonexistent")

        missed = self.registry._missed_evolutions.get(self.monster_id, [])
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0].slug, slug)

    def test_clear_pending_nonexistent_slug(self):
        slug = "fire"

        self.registry.add_pending(self.monster_id, slug)
        self.registry.clear_pending_slug(self.monster_id, "nonexistent")

        pending = self.registry.get_pending(self.monster_id)
        self.assertEqual(pending, [slug])
