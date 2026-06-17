# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def filter_odoo_x2many_commands(commands, keep_ids):
    """
    Returns x2many commands preserving only 'keep_ids'.
    """
    result = []
    if not commands:
        return result
        
    # If a single command was passed somehow (e.g., False was already handled above),
    # ensure it is a list of commands. Odoo sometimes passes [(6, 0, ids)]
    if not isinstance(commands, list) and not isinstance(commands, tuple):
        return result

    for command in commands:
        if command[0] in (1, 2, 3, 4):
            if command[1] in keep_ids:
                result.append(command)
        elif command[0] == 6:
            target_ids = [x for x in command[2] if x in keep_ids]
            if target_ids:
                result.append((6, 0, target_ids))
        elif command[0] == 5:
            # If the command is 5 (clear all), to preserve keep_ids,
            # we should explicitly keep them by converting it to a 6 command
            # if we have keep_ids to preserve.
            if keep_ids:
                result.append((6, 0, list(keep_ids)))
            else:
                result.append(command)
        else:
            result.append(command)
    return result


def diff_to_odoo_x2many_commands(current_ids, target_ids):
    """
    Returns x2x commands resulting in diff between current and target.
    """
    if type(current_ids) is not set:
        current_ids = set(current_ids)
    if type(target_ids) is not set:
        target_ids = set(target_ids)

    result = []
    if current_ids ^ target_ids:
        if target_ids - current_ids:
            result.extend([(4, g) for g in list(target_ids - current_ids)])
        if current_ids - target_ids:
            result.extend([(3, g) for g in list(current_ids - target_ids)])
    return result


def play_odoo_x2x_commands_on_ids(in_ids, commands):
    """
    Returns the ids that will be preserved.
    """
    result_ids = set(in_ids)
    for command in commands:
        if command[0] == 3:
            result_ids -= {command[1]}
        elif command[0] == 4:
            result_ids |= {command[1]}
        elif command[0] == 5:
            result_ids = set()
        elif command[0] == 6:
            result_ids = set(command[2])
        else:  # 0, 1, 2
            raise NotImplementedError
    return result_ids
