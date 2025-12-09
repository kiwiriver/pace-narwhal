import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress, gaussian_kde
import matplotlib as mpl
from scipy import stats
from sklearn.linear_model import HuberRegressor, TheilSenRegressor
from sklearn.preprocessing import StandardScaler
import warnings

# Set publication-quality defaults
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.linewidth': 1.2,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
    'lines.linewidth': 1.5,
    'patch.linewidth': 0.5,
    'text.usetex': False,
})

def robust_regression(x, y, method='ols'):
    """
    Perform robust regression with multiple method options.
    
    Parameters:
    -----------
    x, y : array-like
        Input data
    method : str
        Regression method:
        - 'ols': Ordinary Least Squares (scipy.stats.linregress)
        - 'huber': Huber regression (robust to outliers)
        - 'theil_sen': Theil-Sen estimator (very robust, median-based)
        - 'ransac': RANSAC (RANdom SAmple Consensus)
        
    Returns:
    --------
    dict with keys: slope, intercept, r_value, p_value, std_err, method_used
    """
    from sklearn.linear_model import RANSACRegressor
    
    x = np.asarray(x).reshape(-1, 1) if len(np.asarray(x).shape) == 1 else np.asarray(x)
    y = np.asarray(y)
    
    if len(x) < 2:
        return {
            'slope': np.nan, 'intercept': np.nan, 'r_value': np.nan,
            'p_value': np.nan, 'std_err': np.nan, 'method_used': method
        }
    
    # Remove infinite values
    mask = np.isfinite(x.flatten()) & np.isfinite(y)
    if np.sum(mask) < 2:
        return {
            'slope': np.nan, 'intercept': np.nan, 'r_value': np.nan,
            'p_value': np.nan, 'std_err': np.nan, 'method_used': method
        }
    
    x_clean = x[mask]
    y_clean = y[mask]
    
    try:
        if method == 'ols':
            # Standard scipy linear regression
            slope, intercept, r_value, p_value, std_err = linregress(x_clean.flatten(), y_clean)
            return {
                'slope': slope, 'intercept': intercept, 'r_value': r_value,
                'p_value': p_value, 'std_err': std_err, 'method_used': 'OLS'
            }
            
        elif method == 'huber':
            # Huber regression - robust to outliers
            huber = HuberRegressor(epsilon=1.35, max_iter=200, alpha=0.0)
            huber.fit(x_clean, y_clean)
            slope = huber.coef_[0] if len(huber.coef_) == 1 else huber.coef_[0]
            intercept = huber.intercept_
            
            # Calculate R-squared manually
            y_pred = slope * x_clean.flatten() + intercept
            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            r_value = np.sqrt(max(0, r_squared)) * np.sign(slope)
            
            return {
                'slope': slope, 'intercept': intercept, 'r_value': r_value,
                'p_value': np.nan, 'std_err': np.nan, 'method_used': 'Huber'
            }
            
        elif method == 'theil_sen':
            # Theil-Sen estimator - very robust, uses median
            theil_sen = TheilSenRegressor(max_subpopulation=1e4, n_subsamples=None, 
                                        max_iter=300, tol=1e-3, random_state=42)
            theil_sen.fit(x_clean, y_clean)
            slope = theil_sen.coef_[0] if len(theil_sen.coef_) == 1 else theil_sen.coef_[0]
            intercept = theil_sen.intercept_
            
            # Calculate R-squared
            y_pred = slope * x_clean.flatten() + intercept
            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            r_value = np.sqrt(max(0, r_squared)) * np.sign(slope)
            
            return {
                'slope': slope, 'intercept': intercept, 'r_value': r_value,
                'p_value': np.nan, 'std_err': np.nan, 'method_used': 'Theil-Sen'
            }
            
        elif method == 'ransac':
            # RANSAC - very robust to outliers
            ransac = RANSACRegressor(random_state=42, max_trials=100, 
                                   min_samples=max(2, int(0.5 * len(x_clean))))
            ransac.fit(x_clean, y_clean)
            slope = ransac.estimator_.coef_[0]
            intercept = ransac.estimator_.intercept_
            
            # Calculate R-squared using inlier mask
            inlier_mask = ransac.inlier_mask_
            if np.sum(inlier_mask) > 1:
                y_pred_inliers = slope * x_clean[inlier_mask].flatten() + intercept
                ss_res = np.sum((y_clean[inlier_mask] - y_pred_inliers) ** 2)
                ss_tot = np.sum((y_clean[inlier_mask] - np.mean(y_clean[inlier_mask])) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                r_value = np.sqrt(max(0, r_squared)) * np.sign(slope)
            else:
                r_value = 0
            
            return {
                'slope': slope, 'intercept': intercept, 'r_value': r_value,
                'p_value': np.nan, 'std_err': np.nan, 'method_used': f'RANSAC ({np.sum(inlier_mask)}/{len(x_clean)})'
            }
            
        else:
            raise ValueError(f"Unknown regression method: {method}")
            
    except Exception as e:
        warnings.warn(f"Robust regression failed with method '{method}': {e}. Falling back to OLS.")
        # Fallback to OLS
        try:
            slope, intercept, r_value, p_value, std_err = linregress(x_clean.flatten(), y_clean)
            return {
                'slope': slope, 'intercept': intercept, 'r_value': r_value,
                'p_value': p_value, 'std_err': std_err, 'method_used': 'OLS (fallback)'
            }
        except:
            return {
                'slope': np.nan, 'intercept': np.nan, 'r_value': np.nan,
                'p_value': np.nan, 'std_err': np.nan, 'method_used': f'{method} (failed)'
            }

def color_kde_scatter(ax, x, y, s=20, alpha=0.7, cmap='viridis'):
    """
    Create a scatter plot colored by 2D KDE density with publication quality.
    """
    if len(x) == 0 or len(y) == 0:
        return None
        
    # Calculate the point density
    xy = np.vstack([x, y])
    
    if len(x) > 1:
        try:
            kde = gaussian_kde(xy)
            density = kde(xy)
        except (np.linalg.LinAlgError, ValueError):
            # Fallback if KDE fails (e.g., singular matrix)
            density = np.ones(len(x))
    else:
        density = np.ones(len(x))
    
    # Sort points by density (lowest first)
    idx = density.argsort()
    x_sorted, y_sorted, density_sorted = x[idx], y[idx], density[idx]
    
    # Create scatter plot
    scatter = ax.scatter(x_sorted, y_sorted, c=density_sorted, 
                        s=s, alpha=alpha, cmap=cmap,
                        edgecolors='white', linewidths=0.1)
    
    return scatter

def plot_corr_one_density_kde(
    x, y, label, title=None, fileout=None,
    xlabel="Validation Target", ylabel="PACE", buffer_frac=0.1,
    layout=(2, 2), figsize=None, style='publication',
    reference_method='x',  # 'x', 'y', or 'mean'
    subplot_labels=True,  # Add (a), (b), (c), (d) labels
    regression_method='ols',  # 'ols', 'huber', 'theil_sen', 'ransac'
    show_confidence_intervals=True,  # Show confidence intervals for regression
    outlier_detection=False,  # Highlight potential outliers
    outlier_threshold=2.5  # Standard deviations for outlier detection
):
    """
    Create publication-quality correlation plots with robust regression options.
    
    Parameters:
    -----------
    x, y : array-like
        Data arrays to compare
    label : str
        Label for the data (legacy parameter, kept for compatibility)
    title : str, optional
        Main title for the first subplot
    fileout : str, optional
        Output filename for saving the plot
    xlabel, ylabel : str
        Labels for x and y axes
    buffer_frac : float, default 0.1
        Fraction of data range to add as buffer around plot limits
    layout : tuple, default (2, 2)
        Layout configuration as (rows, cols)
    figsize : tuple, optional
        Figure size. If None, automatically determined based on layout
    style : str, default 'publication'
        Plot style ('publication', 'presentation', 'minimal')
    reference_method : str, default 'x'
        - 'x': Use x as reference (x vs y-x) - when x is truth/standard
        - 'y': Use y as reference (y vs x-y) - when y is truth/standard
        - 'mean': Classical Bland-Altman (mean of x,y vs difference)
    subplot_labels : bool, default True
        Add (a), (b), (c), (d) labels to subplots
    regression_method : str, default 'ols'
        Regression method: 'ols', 'huber', 'theil_sen', 'ransac'
    show_confidence_intervals : bool, default True
        Show confidence intervals for OLS regression
    outlier_detection : bool, default False
        Highlight potential outliers in scatter plot
    outlier_threshold : float, default 2.5
        Standard deviations for outlier detection
    """
    
    # Style configurations (same as before)
    styles = {
        'publication': {
            'scatter_size': 15,
            'scatter_alpha': 0.7,
            'line_width': 1.5,
            'grid_alpha': 0.3,
            'text_bbox': dict(boxstyle='round,pad=0.3', facecolor='white', 
                             alpha=0.9, edgecolor='gray', linewidth=0.5),
            'colors': {'primary': '#2E86AB', 'secondary': '#A23B72', 
                      'accent': '#F18F01', 'neutral': '#C73E1D'},
            'cmap': 'viridis'
        },
        'presentation': {
            'scatter_size': 20,
            'scatter_alpha': 0.8,
            'line_width': 2.0,
            'grid_alpha': 0.4,
            'text_bbox': dict(boxstyle='round,pad=0.4', facecolor='white', 
                             alpha=0.95, edgecolor='black', linewidth=1),
            'colors': {'primary': '#1f77b4', 'secondary': '#ff7f0e', 
                      'accent': '#2ca02c', 'neutral': '#d62728'},
            'cmap': 'plasma'
        },
        'minimal': {
            'scatter_size': 12,
            'scatter_alpha': 0.6,
            'line_width': 1.0,
            'grid_alpha': 0.2,
            'text_bbox': dict(boxstyle='square,pad=0.3', facecolor='white', 
                             alpha=0.8, edgecolor='none'),
            'colors': {'primary': '#333333', 'secondary': '#666666', 
                      'accent': '#999999', 'neutral': '#cccccc'},
            'cmap': 'gray'
        }
    }
    
    current_style = styles.get(style, styles['publication'])
    
    x = np.asarray(x)
    y = np.asarray(y)

    # Remove NaNs and infs from both
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = len(x)

    # Outlier detection
    outlier_mask = np.zeros(n, dtype=bool)
    if outlier_detection and n > 4:
        # Use residuals from initial OLS fit to identify outliers
        if n > 1:
            try:
                temp_slope, temp_intercept, _, _, _ = linregress(x, y)
                residuals = y - (temp_slope * x + temp_intercept)
                residual_std = np.std(residuals)
                outlier_mask = np.abs(residuals) > outlier_threshold * residual_std
            except:
                outlier_mask = np.zeros(n, dtype=bool)

    if n == 0:
        min1, max1 = 0, 1
    else:
        allvals = np.concatenate([x, y])
        data_min = float(np.nanmin(allvals))
        data_max = float(np.nanmax(allvals))
        data_range = data_max - data_min if data_max > data_min else 1
        min1 = data_min - buffer_frac * data_range
        max1 = data_max + buffer_frac * data_range

    # Determine reference values and differences based on reference_method
    if reference_method == 'x':
        ref_vals = x.copy()
        diff_vals = y - x
        ref_label = xlabel
        bias_direction = f"{ylabel} − {xlabel}"
        analysis_title = ""
    elif reference_method == 'y':
        ref_vals = y.copy()
        diff_vals = x - y
        ref_label = ylabel
        bias_direction = f"{xlabel} − {ylabel}"
        analysis_title = ""
    else:  # reference_method == 'mean'
        ref_vals = (x + y) / 2 if n > 0 else np.array([])
        diff_vals = y - x if n > 0 else np.array([])
        ref_label = f"Mean of {xlabel} and {ylabel}"
        bias_direction = f"{ylabel} − {xlabel}"
        analysis_title = ""

    # Perform robust regression
    reg_results = robust_regression(x, y, method=regression_method)
    slope = reg_results['slope']
    intercept = reg_results['intercept']
    r_value = reg_results['r_value']
    p_value = reg_results['p_value']
    std_err = reg_results['std_err']
    method_used = reg_results['method_used']

    # Basic statistics
    corr = np.corrcoef(x, y)[0, 1] if n > 1 else np.nan
    mean_diff = np.mean(diff_vals) if n > 0 else np.nan
    std_diff = np.std(diff_vals, ddof=1) if n > 1 else np.nan
    
    if n > 1:
        rmse = np.sqrt(np.mean((y - x)**2))
        mae = np.mean(np.abs(y - x))
    else:
        rmse, mae = np.nan, np.nan

    # Additional metrics for reference method
    if reference_method != 'mean' and n > 0:
        percent_bias = (mean_diff / np.mean(ref_vals)) * 100 if np.mean(ref_vals) != 0 else np.nan
        relative_std = (std_diff / np.mean(ref_vals)) * 100 if np.mean(ref_vals) != 0 else np.nan
    else:
        percent_bias = relative_std = np.nan

    # Auto-determine figure size if not provided
    if figsize is None:
        base_size = 4 if style == 'publication' else 4.5
        if layout == (2, 2):
            figsize = (base_size * 2.4, base_size * 2.2)
        elif layout == (1, 4):
            figsize = (base_size * 4.4, base_size * 1.3)
        elif layout == (4, 1):
            figsize = (base_size * 1.3, base_size * 4.4)
        else:
            figsize = (layout[1] * base_size * 1.1, layout[0] * base_size * 1.1)

    # Validate layout
    if layout[0] * layout[1] < 4:
        raise ValueError("Layout must accommodate at least 4 subplots")

    # Create figure
    fig = plt.figure(figsize=figsize, constrained_layout=False)
    
    # Create subplots with specific spacing
    if layout == (2, 2):
        gs = fig.add_gridspec(2, 2, left=0.12, bottom=0.08, right=0.98, top=0.92,
                             wspace=0.3, hspace=0.35)
    elif layout == (1, 4):
        gs = fig.add_gridspec(1, 4, left=0.08, bottom=0.15, right=0.98, top=0.85,
                             wspace=0.4, hspace=0.3)
    elif layout == (4, 1):
        gs = fig.add_gridspec(4, 1, left=0.15, bottom=0.05, right=0.95, top=0.95,
                             wspace=0.3, hspace=0.4)
    else:
        gs = fig.add_gridspec(layout[0], layout[1], left=0.12, bottom=0.08, 
                             right=0.98, top=0.92, wspace=0.3, hspace=0.35)
    
    # Create axes
    axes = []
    for i in range(min(4, layout[0] * layout[1])):
        row = i // layout[1]
        col = i % layout[1]
        ax = fig.add_subplot(gs[row, col])
        axes.append(ax)

    # Subplot labels
    subplot_letters = ['(a)', '(b)', '(c)', '(d)']

    # Panel 1: Enhanced scatter plot with density coloring and outlier highlighting
    if n > 0:
        # Plot normal points
        normal_mask = ~outlier_mask if outlier_detection else np.ones(n, dtype=bool)
        if np.any(normal_mask):
            scatter = color_kde_scatter(
                axes[0], x[normal_mask], y[normal_mask], 
                s=current_style['scatter_size'], 
                alpha=current_style['scatter_alpha'],
                cmap=current_style['cmap']
            )
        
        # Highlight outliers if requested
        if outlier_detection and np.any(outlier_mask):
            axes[0].scatter(x[outlier_mask], y[outlier_mask], 
                           s=current_style['scatter_size']+10, 
                           alpha=0.8, color='red', marker='x',
                           linewidths=2, label=f'Outliers (n={np.sum(outlier_mask)})')
    
    # 1:1 line
    axes[0].plot([min1, max1], [min1, max1], 'k--', 
                linewidth=current_style['line_width'], 
                label="1:1 line", alpha=0.8)
    
    # Robust regression line
    if n > 1 and not np.isnan(slope):
        reg_x = np.array([min1, max1])
        reg_y = slope * reg_x + intercept
        
        # Enhanced regression line label with method
        reg_label = f"{method_used}: y = {slope:.3f}x + {intercept:.3f}"
        if not np.isnan(r_value):
            reg_label += f" (R={r_value:.3f})"
            
        axes[0].plot(reg_x, reg_y, 
                    color=current_style['colors']['accent'], 
                    linewidth=current_style['line_width'],
                    label=reg_label)
        
        # Add confidence intervals for OLS
        if (show_confidence_intervals and regression_method == 'ols' and 
            not np.isnan(std_err) and n > 4):
            try:
                # Calculate confidence intervals
                t_val = stats.t.ppf(0.975, n-2)  # 95% confidence
                x_range = np.linspace(min1, max1, 100)
                y_fit = slope * x_range + intercept
                
                # Standard error of prediction
                x_mean = np.mean(x)
                sxx = np.sum((x - x_mean)**2)
                residuals = y - (slope * x + intercept)
                mse = np.sum(residuals**2) / (n - 2)
                
                se_pred = np.sqrt(mse * (1 + 1/n + (x_range - x_mean)**2 / sxx))
                ci_upper = y_fit + t_val * se_pred
                ci_lower = y_fit - t_val * se_pred
                
                axes[0].fill_between(x_range, ci_lower, ci_upper, 
                                   alpha=0.2, color=current_style['colors']['accent'],
                                   label='95% CI')
            except:
                pass  # Skip CI if calculation fails
    
    axes[0].set_xlim(min1, max1)
    axes[0].set_ylim(min1, max1)
    axes[0].set_xlabel(xlabel, fontweight='bold')
    axes[0].set_ylabel(ylabel, fontweight='bold')
    axes[0].set_aspect('equal', adjustable='box')
    
    if title is not None:
        axes[0].set_title(title, fontweight='bold', pad=15)
    
    axes[0].legend(loc="upper left", framealpha=0.9, fontsize=9)

    # Enhanced statistics text for Panel 1
    txt1 = (
        f"n = {n:,}\n"
        f"R = {corr:.3f}\n"
        f"RMSE = {rmse:.3f}\n"
        f"MAE = {mae:.3f}"
    )
    
    if outlier_detection and np.any(outlier_mask):
        txt1 += f"\nOutliers = {np.sum(outlier_mask)}"
    
    axes[0].text(
        0.95, 0.05, txt1, transform=axes[0].transAxes,
        fontsize=10, va='bottom', ha='right',
        bbox=current_style['text_bbox']
    )

    # Panels 2, 3, 4 remain largely the same as your original code
    # ... (continuing with the rest of the panels as in your original function)
    # I'll include the key parts but truncate for space

    # Panel 2: Reference-based bias analysis (same as original with minor enhancements)
    if n > 0:
        color_kde_scatter(
            axes[1], ref_vals, diff_vals, 
            s=current_style['scatter_size']-3, 
            alpha=current_style['scatter_alpha'],
            cmap=current_style['cmap']
        )
        
        if len(ref_vals) > 0:
            ref_min = float(np.nanmin(ref_vals))
            ref_max = float(np.nanmax(ref_vals))
            ref_range = ref_max - ref_min if ref_max > ref_min else 1
            ba_min = ref_min - buffer_frac * ref_range
            ba_max = ref_max + buffer_frac * ref_range
            axes[1].set_xlim(ba_min, ba_max)
        
        if len(diff_vals) > 0:
            diff_min = float(np.nanmin(diff_vals))
            diff_max = float(np.nanmax(diff_vals))
            diff_range = diff_max - diff_min if diff_max > diff_min else 1
            ba_ymin = diff_min - buffer_frac * diff_range
            ba_ymax = diff_max + buffer_frac * diff_range
            axes[1].set_ylim(ba_ymin, ba_ymax)

    # Reference lines
    axes[1].axhline(0, color='k', linestyle='--', 
                   linewidth=current_style['line_width'], alpha=0.8,
                   label='Zero bias')

    if not np.isnan(mean_diff) and not np.isnan(std_diff):
        axes[1].axhline(mean_diff, color=current_style['colors']['accent'], 
                       linestyle='-', linewidth=current_style['line_width'],
                       label=f"Mean bias: {mean_diff:.3f}")
        
        limit_multiplier = 1.96 if reference_method == 'mean' else 2.0
        upper_limit = mean_diff + limit_multiplier * std_diff
        lower_limit = mean_diff - limit_multiplier * std_diff
        
        axes[1].axhline(upper_limit, 
                       color=current_style['colors']['secondary'], 
                       linestyle=':', linewidth=current_style['line_width'],
                       alpha=0.8, label=f"±{limit_multiplier:.1f}σ limits")
        axes[1].axhline(lower_limit, 
                       color=current_style['colors']['secondary'], 
                       linestyle=':', linewidth=current_style['line_width'],
                       alpha=0.8)

    axes[1].set_xlabel(ref_label, fontweight='bold')
    axes[1].set_ylabel(f"{bias_direction}", fontweight='bold')
    axes[1].set_title(analysis_title, fontweight='bold', pad=15)
    axes[1].legend(loc="upper right", framealpha=0.95, fontsize=9)

    # Statistics text for Panel 2
    if reference_method != 'mean':
        txt2 = (
            f"n = {n:,}\n"
            f"Bias = {mean_diff:.4f}\n"
            f"SD = {std_diff:.4f}\n"
            f"Rel. bias = {percent_bias:.2f}%\n"
            f"Rel. SD = {relative_std:.2f}%"
        )
    else:
        txt2 = (
            f"n = {n:,}\n"
            f"Bias = {mean_diff:.4f}\n"
            f"SD = {std_diff:.4f}\n"
            f"95% LoA = ±{1.96*std_diff:.3f}" if not np.isnan(std_diff) else "SD = NaN"
        )
    
    axes[1].text(
        0.05, 0.95, txt2, transform=axes[1].transAxes,
        fontsize=10, va='top', ha='left',
        bbox=current_style['text_bbox']
    )

    # Panels 3 and 4: Keep the same as your original implementation
    # Panel 3: Histograms
    if n > 0:
        bins = np.linspace(min1, max1, min(30, max(10, n//10)))
        
        axes[2].hist(x, bins=bins, alpha=0.6, 
                    label=xlabel, 
                    color=current_style['colors']['primary'],
                    edgecolor='white', linewidth=0.5)
        axes[2].hist(y, bins=bins, alpha=0.6, 
                    label=ylabel, 
                    color=current_style['colors']['secondary'],
                    edgecolor='white', linewidth=0.5)
        
        axes[2].set_xlabel("Value", fontweight='bold')
        axes[2].set_ylabel("Frequency", fontweight='bold')
        axes[2].set_title("", fontweight='bold', pad=15)
        axes[2].legend(loc="best", framealpha=0.9, fontsize=9)
        
        txt3 = (
            f"{xlabel}: μ={np.mean(x):.3f}, σ={np.std(x):.3f}\n"
            f"{ylabel}: μ={np.mean(y):.3f}, σ={np.std(y):.3f}"
        )
        axes[2].text(
            0.95, 0.95, txt3, transform=axes[2].transAxes,
            fontsize=9, va='top', ha='right',
            bbox=current_style['text_bbox']
        )

#####
    
    # Panel 4: Difference distribution
    if n > 0:
        diff_std = np.std(diff_vals)
        diff_range = max(abs(np.min(diff_vals)), abs(np.max(diff_vals)))
        diff_bins = np.linspace(-diff_range*1.2, diff_range*1.2, 
                               min(30, max(10, n//10)))
        
        counts, bins_edges, patches = axes[3].hist(
            diff_vals, bins=diff_bins, alpha=0.7, 
            color=current_style['colors']['primary'],
            edgecolor='white', linewidth=0.5
        )
        
        # Reference lines
        axes[3].axvline(0, color='k', linestyle='--', 
                       linewidth=current_style['line_width'], alpha=0.8,
                       label='Zero bias')
        axes[3].axvline(mean_diff, color=current_style['colors']['accent'], 
                       linestyle='-', linewidth=current_style['line_width'],
                       label=f"Mean: {mean_diff:.3f}")
        
        if not np.isnan(std_diff):
            # Only label one of the ±1σ lines
            axes[3].axvline(mean_diff + std_diff, 
                           color=current_style['colors']['secondary'], 
                           linestyle=':', linewidth=current_style['line_width'],
                           alpha=0.8, label=f"±1σ")
            axes[3].axvline(mean_diff - std_diff, 
                           color=current_style['colors']['secondary'], 
                           linestyle=':', linewidth=current_style['line_width'],
                           alpha=0.8)  # No label
        
        axes[3].set_xlabel(f"{bias_direction}", fontweight='bold')
        axes[3].set_ylabel("Frequency", fontweight='bold')
        title1="Residual Analysis"
        title1=""
        axes[3].set_title(title1, fontweight='bold', pad=15)
        axes[3].legend(loc="best", framealpha=0.9, fontsize=9)
        
        # Normality test info
        if n > 8:  # Minimum sample size for meaningful normality test
            _, p_norm = stats.normaltest(diff_vals)
            norm_text = f"Normality p-val: {p_norm:.3f}"
        else:
            norm_text = "N too small for test"
            
        txt4 = (
            f"n = {n:,}\n"
            f"Skewness: {stats.skew(diff_vals):.3f}\n"
            f"Kurtosis: {stats.kurtosis(diff_vals):.3f}\n"
            f"{norm_text}"
        )
        axes[3].text(
            0.95, 0.95, txt4, transform=axes[3].transAxes,
            fontsize=9, va='top', ha='right',
            bbox=current_style['text_bbox']
        )
    else:
        axes[3].text(0.5, 0.5, "No data available", 
                    ha='center', va='center', transform=axes[3].transAxes,
                    fontsize=12, style='italic')

    # Add aligned subplot labels outside plot area
    if subplot_labels:
        for i, ax in enumerate(axes):
            # Position labels consistently relative to figure coordinates
            # Get subplot position in figure coordinates
            bbox = ax.get_position()
            
            # Place label at consistent position relative to subplot
            #bbox.x0 - 0.06, bbox.y1 + 0.02
            fig.text(bbox.x0 - 0.06, bbox.y1, subplot_letters[i], 
                    fontsize=16, fontweight='bold', 
                    ha='center', va='bottom')
    
    # Add overall title if specified
    if title and layout == (2, 2):
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.96)
    
    # Save with high quality
    if fileout:
        plt.savefig(fileout, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    plt.show()