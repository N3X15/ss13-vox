import os
from buildtools import ENV
from buildtools.maestro import BuildMaestro
from buildtools.maestro.web import UglifyJSTarget, DartSCSSBuildTarget
from buildtools.maestro.coffeescript import CoffeeBuildTarget
from buildtools.maestro.package_managers import YarnBuildTarget

NODE_MODULES_DIR = os.path.abspath(os.path.join('node_modules','.bin'))
ENV.prependTo('PATH', NODE_MODULES_DIR)
COFFEE = os.path.join(NODE_MODULES_DIR, 'coffee')
UGLIFY = os.path.join(NODE_MODULES_DIR, 'uglifyjs')
SCSS = os.path.join(NODE_MODULES_DIR, 'scss')
bm: BuildMaestro = BuildMaestro()
yarn = bm.add(YarnBuildTarget())
def mkCoffee(basefilename):
    coffee = bm.add(CoffeeBuildTarget(os.path.join('dist', 'code', 'modules', 'html_interface', f'{basefilename}.js'), [os.path.join('coffee', f'{basefilename}.coffee')], dependencies=[yarn.target], coffee_executable=COFFEE))
    coffee.coffee_opts += ['--transpile'] # Babel
    bm.add(UglifyJSTarget(os.path.join('dist', 'code', 'modules', 'html_interface', f'{basefilename}.min.js'), coffee.target, uglify_executable=UGLIFY))
mkCoffee('aivoice')
bm.add(DartSCSSBuildTarget(os.path.join('dist', 'html', 'browser', 'aivoice.css'), [os.path.join('scss', 'style.scss')], dependencies=[yarn.target]))
bm.as_app()
