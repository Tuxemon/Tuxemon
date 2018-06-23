import logging
logger = logging.getLogger(__name__) #import the logger
import random


from tuxemon.core.components.technique import Technique

##############
# base class #
##############
class effect(object):
    """A class that do an effect on a pokemon ( for item or move )"""
    name = "undefined_effect_name"

    def __init__(self, param={"power" : 0, "technique" : None}):
        self.param = param

    def execute(self, user, target):
        return {"success" : False}


########
# heal #
########
class heal(effect):
    name = "heal"
    def execute(self, user, target):
        retour = {"success" : False}

        if target.is_healed(): # target is healable ?
            retour["success"] = False
            return retour

        target.heal(self.param["power"])
        retour["success"] = True
        return retour


###########
# capture #
###########
class capture(effect):
    name = "capture"
    def execute(self, user, target):
        """Captures target monster.

        :param user: The monster or object that is using this item.
        :param target: The monster or object that we are using this item on.

        :type user: Varies
        :type target: Varies

        :rtype: bool
        :returns: Success
        """
        # Set up variables for capture equation
        damage_modifier = 0
        status_modifier = 0
        item_power = self.param["power"]

        # Get percent of damage taken and multiply it by 10
        if target.current_hp < target.hp:
            total_damage = target.hp - target.current_hp
            damage_modifier = int((float(total_damage) / target.hp) * 1000)

        # Check if target has any status effects
        if not target.status == "Normal":
            status_modifier = 1.5

        # TODO: debug logging this info

        # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
        catch_check = (3 * target.hp - 2 * target.current_hp) * target.catch_rate * item_power * status_modifier / (
        3 * target.hp)
        shake_check = 65536 / (255 / catch_check) ** 0.1875

        logger.debug("--- Capture Variables ---")
        logger.debug("(3*target.hp - 2*target.current_hp) * target.catch_rate * item_power * status_modifier / (3*target.hp)")

        msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"
        logger.debug(msg.format(target, item_power, status_modifier))

        logger.debug("65536 / (255 / catch_check) ** 0.1875")
        logger.debug("65536 / (255 / {}) ** 0.1875".format(catch_check))

        msg = "Each shake has a {} chance of breaking the creature free. (shake_check = {})"
        logger.debug(msg.format(round((65536 - shake_check) / 65536, 2), round(shake_check)))

        # 4 shakes to give monster change to escape
        for i in range(0, 4):
            random_num = random.randint(0, 65536)
            logger.debug("shake check {}: random number {}".format(i, random_num))
            if random_num > round(shake_check):
                return {"success": False,
                        "capture": True,
                        "num_shakes": i + 1}

        # add creature to the player's monster list
        user.add_monster(target)

        # TODO: remove monster from the other party
        return {"success": True,
                "capture": True,
                "num_shakes": 4}


##########
# damage #
##########
class damage(effect):
    name = "damage"
    def calculate_damage(self, user, target):
        """ Calc. damage for the damage technique

        :param user: The Monster object that used this technique.
        :param target: The Monster object that we are using this technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: int
        """
        # Original Pokemon battle damage formula:
        # according to: http://www.math.miami.edu/~jam/azure/compendium/battdam.htm
        # ((2 * user.level / 7) * user.attack * self.power) / target.defense) / 50) +2) * stab_bonus) * type_modifiers/10) * random.randrange(217, 255))/255

        tech = self.param["technique"]
        power = tech.power

        if tech.category == "physical":
            level_modifier = ((2 * user.level) / 7.)
            attack_modifier = user.attack * power
            return int(((level_modifier * attack_modifier) / float(target.defense)) / 50.)

        elif tech.category == "special":
            level_modifier = ((2 * user.level) / 7.)
            attack_modifier = user.special_attack * power
            return int(((level_modifier * attack_modifier) / float(target.special_defense)) / 50.)

        elif tech.category == "poison":
            return int(power)

        logger.error('unhandled damage category')
        raise RuntimeError

    def execute(self, user, target):
        """ This effect applies damage to a target monster. Damage calculations are based upon the
        original Pokemon battle damage formula. This effect will be applied if "damage" is defined
        in this technique's effect list.

        :param user: The Monster object that used this technique.
        :param target: The Monster object that we are using this technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: dict
        """
        damage = self.calculate_damage(user, target)

        # TODO: handle tacking damage by the monster
        if damage:
            target.current_hp -= damage

        return {
            'damage': damage,
            'should_tackle': bool(damage),
            'success': bool(damage),
            'toPlay' : "attack"
        }

##########
# poison #
##########
class poison(effect):
    name = "poison"
    def execute(self, user, target):
        """ This effect has a chance to apply the poison status effect to a target monster.
        Currently there is a 1/10 chance of poison.

        :param user: The Monster object that used this technique.
        :param target: The Monster object that we are using this technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: dict
        """
        already_poisoned = any(t for t in target.status if t.slug == "status_poison")

        if not already_poisoned and random.randrange(1, 2) == 1:
            target.apply_status(Technique("status_poison"))
            success = True
        else:
            success = False

        return {
            'should_tackle': success,
            'success': success,
        }

#########
# faint #
#########
class faint(effect):
    name = "faint"
    def execute(self, user, target):
        """ Faint this monster.  Typically, called by combat to faint self, not others.

        :param user: The Monster object that used this technique.
        :param target: The Monster object that we are using this technique on.

        :type user: core.components.monster.Monster
        :type target: core.components.monster.Monster

        :rtype: dict
        """
        # TODO: implement into the combat state, currently not used

        already_fainted = any(t for t in target.status if t.name == "status_faint")

        if already_fainted:
            raise RuntimeError

        target.apply_status(Technique("status_faint"))

        return {
            'should_tackle': False,
            'success': True,
        }

class swap(effect):
    name = "swap"
    def execute(self, user, target):
        """ Used just for combat: change order of monsters

        Position of monster in party will be changed

        :param user: core.components.monster.Monster
        :param target: core.components.monster.Monster

        :rtype: dict
        """
        # TODO: implement actions as events, so that combat state can find them
        # TODO: relies on setting "combat_state" attribute.  maybe clear it up later
        # TODO: these values are set in combat_menus.py

        def swap_add():
            # rearrange the trainer's monster list
            monster_list = user.monsters
            original_index = monster_list.index(original_monster)
            target_index = monster_list.index(target)
            monster_list[original_index] = target
            monster_list[target_index] = original_monster

            # TODO: make accommodations for battlefield positions
            # add the monster into play
            combat_state.add_monster_into_play(user, target)

        # TODO: find a way to pass values. this will only work for SP games with one monster party
        # get the original monster to be swapped out
        original_monster = user.monsters[0]
        combat_state = self.param["technique"].combat_state

        # rewrite actions to target the new monster.  must be done before original is removed
        combat_state.rewrite_action_queue_target(original_monster, target)

        # remove the old monster and all their actions
        combat_state.remove_monster_from_play(user, original_monster)

        # give a slight delay
        combat_state.task(swap_add, .75)
        combat_state.suppress_phase_change(.75)

        return {
            'success': True,
            'should_tackle': False,
        }
