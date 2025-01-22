import contextlib
from argcomplete.completers import FilesCompleter

from milc import cli
from milc.attrdict import AttrDict

import qmk.path
from qmk.commands import dump_lines, parse_configurator_json
from qmk.constants import GPL2_HEADER_C_LIKE, GENERATED_HEADER_C_LIKE


class ModuleAPI(AttrDict):
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            self[key] = value


MODULE_API_LIST = [
    ModuleAPI(ret_type='void', name='keyboard_pre_init', args='void', call_params='', ret_val=None, guard=None),
    ModuleAPI(ret_type='void', name='keyboard_post_init', args='void', call_params='', ret_val=None, guard=None),
    ModuleAPI(ret_type='bool', name='pre_process_record', args='uint16_t keycode, keyrecord_t *record', call_params='keycode, record', ret_val='true', guard=None),
    ModuleAPI(ret_type='bool', name='process_record', args='uint16_t keycode, keyrecord_t *record', call_params='keycode, record', ret_val='true', guard=None),
    ModuleAPI(ret_type='void', name='post_process_record', args='uint16_t keycode, keyrecord_t *record', call_params='keycode, record', ret_val=None, guard=None),
    ModuleAPI(ret_type='void', name='housekeeping_task', args='void', call_params='', ret_val=None, guard=None),
    ModuleAPI(ret_type='void', name='suspend_power_down', args='void', call_params='', ret_val=None, guard=None),
    ModuleAPI(ret_type='void', name='suspend_wakeup_init', args='void', call_params='', ret_val=None, guard=None),
    ModuleAPI(ret_type='bool', name='shutdown', args='bool jump_to_bootloader', call_params='jump_to_bootloader', ret_val='true', guard=None),
    ModuleAPI(ret_type='bool', name='process_detected_host_os', args='os_variant_t os', call_params='os', ret_val='true', guard="defined(OS_DETECTION_ENABLE)"),
]

MODULE_API_VERSION = '20250122'


@contextlib.contextmanager
def api_guard(lines, api):
    if api.guard:
        lines.append(f'#if {api.guard}')
    yield
    if api.guard:
        lines.append(f'#endif  // {api.guard}')


@cli.argument('-o', '--output', arg_only=True, type=qmk.path.normpath, help='File to write to')
@cli.argument('-q', '--quiet', arg_only=True, action='store_true', help="Quiet mode, only output error messages")
@cli.argument('filename', type=qmk.path.FileType('r'), arg_only=True, completer=FilesCompleter('.json'), help='Configurator JSON file')
@cli.subcommand('Creates a community_modules.h from a keymap.json file.')
def generate_community_modules_h(cli):
    """Creates a community_modules.h from a keymap.json file
    """
    if cli.args.output and cli.args.output.name == '-':
        cli.args.output = None

    lines = [
        GPL2_HEADER_C_LIKE,
        GENERATED_HEADER_C_LIKE,
        '#pragma once',
        '#include <stdint.h>',
        '#include <stdbool.h>',
        '',
        f'#define COMMUNITY_MODULES_API_VERSION {MODULE_API_VERSION}',
        f'#define ASSERT_COMMUNITY_MODULES_MIN_API_VERSION(x) _Static_assert((x) <= COMMUNITY_MODULES_API_VERSION, "Community module requires higher version of QMK modules API -- needs: " #x ", current: {MODULE_API_VERSION}.")',
        '',
        '#ifdef OS_DETECTION_ENABLE',
        '#include "os_detection.h"',
        '#endif // OS_DETECTION_ENABLE',
        '',
        'typedef struct keyrecord_t keyrecord_t;',
    ]

    keymap_json = parse_configurator_json(cli.args.filename)

    if keymap_json and 'modules' in keymap_json:
        for module in keymap_json['modules']:
            lines.append('')
            lines.append(f'// From module: {module}')
            for api in MODULE_API_LIST:
                with api_guard(lines, api):
                    lines.append(f'{api.ret_type} {api.name}_{module}({api.args});')
        lines.append('')

        lines.append('// Core wrapper')
        for api in MODULE_API_LIST:
            with api_guard(lines, api):
                lines.append(f'{api.ret_type} {api.name}_modules({api.args});')

    dump_lines(cli.args.output, lines, cli.args.quiet, remove_repeated_newlines=True)


@cli.argument('-o', '--output', arg_only=True, type=qmk.path.normpath, help='File to write to')
@cli.argument('-q', '--quiet', arg_only=True, action='store_true', help="Quiet mode, only output error messages")
@cli.argument('filename', type=qmk.path.FileType('r'), arg_only=True, completer=FilesCompleter('.json'), help='Configurator JSON file')
@cli.subcommand('Creates a community_modules.c from a keymap.json file.')
def generate_community_modules_c(cli):
    """Creates a community_modules.c from a keymap.json file
    """
    if cli.args.output and cli.args.output.name == '-':
        cli.args.output = None

    lines = [
        GPL2_HEADER_C_LIKE,
        GENERATED_HEADER_C_LIKE,
        '',
        '#include "community_modules.h"',
    ]

    keymap_json = parse_configurator_json(cli.args.filename)

    if keymap_json and 'modules' in keymap_json:

        for module in keymap_json['modules']:
            lines.append('')
            for api in MODULE_API_LIST:
                lines.append('')
                with api_guard(lines, api):
                    lines.append(f'__attribute__((weak)) {api.ret_type} {api.name}_{module}({api.args}) {{')
                    if api.ret_val:
                        lines.append(f'    return {api.ret_val};')
                    lines.append('}')

        for api in MODULE_API_LIST:
            lines.append('')
            with api_guard(lines, api):
                lines.append(f'{api.ret_type} {api.name}_modules({api.args}) {{')
                if api.ret_type == 'bool':
                    lines.append('    return true')
                for module in keymap_json['modules']:
                    if api.ret_type == 'bool':
                        lines.append(f'        && {api.name}_{module}({api.call_params})')
                    else:
                        lines.append(f'    {api.name}_{module}({api.call_params});')
                if api.ret_type == 'bool':
                    lines.append('    ;')
                lines.append('}')

    dump_lines(cli.args.output, lines, cli.args.quiet, remove_repeated_newlines=True)
