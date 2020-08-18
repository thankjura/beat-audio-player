project('beat',
          version: '0.1.0',
    meson_version: '>= 0.51.0'
)

APPLICATION_ID = 'ru.slie.beat'

i18n = import('i18n')
python = import('python')

py_installation = python.find_installation('python3')
if not py_installation.found()
    error('No valid python3 binary found')
endif


pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'beat')


dependency('gtk+-3.0', version: '>= 3.24.7')
dependency('pygobject-3.0', version: '>= 3.36.1')

subdir('data')
subdir('src')
subdir('po')

install_subdir('third_party/tinytag/tinytag', install_dir: moduledir, exclude_directories: ['tests'])

conf = configuration_data()
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('application_id', APPLICATION_ID)

configure_file(
  input: 'beat.in',
  output: 'beat',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

meson.add_install_script('build-aux/meson/postinstall.py')
