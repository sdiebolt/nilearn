import json

import numpy as np
from scipy import sparse
from .. import datasets
from . import cm

from .js_plotting_utils import (add_js_lib, HTMLDocument, mesh_to_plotly,
                                encode, colorscale, get_html_template)


class ConnectomeView(HTMLDocument):
    pass


def _prepare_line(edges, nodes):
    path_edges = np.zeros(len(edges) * 3, dtype=int)
    path_edges[::3] = edges
    path_edges[1::3] = edges
    path_nodes = np.zeros(len(nodes) * 3, dtype=int)
    path_nodes[::3] = nodes[:, 0]
    path_nodes[1::3] = nodes[:, 1]
    return path_edges, path_nodes


def _get_connectome(adjacency_matrix, coords, threshold=None,
                    cmap=cm.cold_hot, symmetric_cmap=True):
    connectome = {}
    coords = np.asarray(coords, dtype='<f4')
    adjacency_matrix = adjacency_matrix.copy()
    colors, vmin, vmax, cmap, norm, abs_threshold = colorscale(
        cmap, adjacency_matrix.ravel(), threshold=threshold,
        symmetric_cmap=symmetric_cmap)
    connectome['colorscale'] = colors
    connectome['cmin'], connectome['cmax'] = float(vmin), float(vmax)
    if threshold is not None:
        adjacency_matrix[np.abs(adjacency_matrix) <= abs_threshold] = 0
    s = sparse.coo_matrix(adjacency_matrix)
    nodes = np.asarray([s.row, s.col], dtype=int).T
    edges = np.arange(len(nodes))
    path_edges, path_nodes = _prepare_line(edges, nodes)
    connectome["_con_w"] = encode(np.asarray(s.data, dtype='<f4')[path_edges])
    c = coords[path_nodes]
    x, y, z = c.T
    for coord, cname in [(x, "x"), (y, "y"), (z, "z")]:
        connectome["_con_{}".format(cname)] = encode(
            np.asarray(coord, dtype='<f4'))
    return connectome


def view_connectome(adjacency_matrix, coords, threshold=None,
                    cmap=cm.cyan_orange, symmetric_cmap=True, embed_js=True):
    """
    Insert a 3d plot of a connectome into an HTML page.

    Parameters
    ----------
    adjacency_matrix : ndarray, shape=(n_nodes, n_nodes)
        the weights of the edges.

    coords : ndarray, shape=(n_nodes, 3)
        the coordinates of the nodes in MNI space.

    threshold : str, number or None, optional (default=None)
        If None, no thresholding.
        If it is a number only connections of amplitude greater
        than threshold will be shown.
        If it is a string it must finish with a percent sign,
        e.g. "25.3%", and only connections of amplitude above the
        given percentile will be shown.

    cmap : str or matplotlib colormap, optional

    symmetric_cmap : bool, optional (default=True)
        Make colormap symmetric (ranging from -vmax to vmax).

    Returns
    -------
    ConnectomeView : plot of the connectome.
        It can be saved as an html page or rendered (transparently) by the
        Jupyter notebook. Useful methods are :

        - 'resize' to resize the plot displayed in a Jupyter notebook
        - 'save_as_html' to save the plot to a file
        - 'open_in_browser' to save the plot and open it in a web browser.

    """
    mesh = datasets.fetch_surf_fsaverage()
    mesh_info = {}
    mesh_info["connectome"] = _get_connectome(
        adjacency_matrix, coords, threshold=threshold, cmap=cmap,
        symmetric_cmap=symmetric_cmap)
    for hemi in ['pial_left', 'pial_right']:
        mesh_info[hemi] = mesh_to_plotly(mesh[hemi])
    as_json = json.dumps(mesh_info)
    as_html = get_html_template('connectome_plot_template.html').replace(
        'INSERT_CONNECTOME_JSON_HERE', as_json)
    as_html = add_js_lib(as_html, embed_js=embed_js)
    return ConnectomeView(as_html)
