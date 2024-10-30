import os
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, AutoLocator
import matplotlib.style as mplstyle
import numpy as np

from ....utils.log import logger

def __wave__(
    dat: np.ndarray,
    time:np.ndarray,
    amp_factor:float = 1.,
    ylabel:str = "Amplitude",
    xlabel:str = "Time",
    title:str = "",
    figsize:tuple = (7,1.5),
    dpi:int = 300,
    savefp:str = None,
    center_mean:bool = True,
    **kwargs,
):
    fig, ax = plt.subplots(1,1,figsize=figsize,dpi=dpi,)

    ax.plot(
        time,
        dat,
        **kwargs,
    )
    
    ax.set_xlim(time.min(), time.max())
    
    if center_mean:
        ymean = np.mean(dat)
        yrange = np.max(np.abs(dat - ymean))*1.2
        ax.set_ylim(ymean - yrange/amp_factor, ymean + yrange/amp_factor)
    else:
        ax.set_ylim(None,None)
        ax.set_ylim(np.array(ax.get_ylim()) / amp_factor)
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    ax.xaxis.set_minor_locator(AutoMinorLocator(10))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_ticks_position('both')
    ax.xaxis.set_ticks_position('both')
    
    ax.grid()
    # ----------------------
    # Save figure
    # ----------------------
    if savefp is not None:
        savedir = os.path.dirname(savefp)
        if not os.path.exists(savedir):
            logger.info(f"Creating directory: {savedir}")
            os.makedirs(savedir)
            
        logger.info(f"Saving {savefp}")
        fig.savefig(savefp, bbox_inches="tight")
    return fig, ax


def __waves__(
    dat: list[np.ndarray],
    time:list[np.ndarray],
    amp_factor:float = 1.,
    chlabel:list[str] = None,
    # ylabel:list[str] = "Amplitude",
    # xlabel:str = "Time",
    title:str = "",
    figsize:tuple = (7,1.0),
    dpi:int = 300,
    center_mean:bool = True,
    savefp:str = None,
    **kwargs,
):
    # mplstyle.use('fast')

    n_fig = len(dat)

    if chlabel is not None:
        if isinstance(chlabel, str):
            chlabel = [chlabel]*n_fig
        if len(chlabel) != n_fig:
            logger.warning(
                "Length of chlabel is not equal to the number of channels. It will be ignored."
            )
            chlabel = None
    
    fig, ax = plt.subplots(
        n_fig, 1,
        figsize=(figsize[0], figsize[1]*n_fig),
        dpi=dpi,
        sharex = True,
        )
    
    for i in range(n_fig):
        ax[i].plot(
            time[i],
            dat[i],
            **kwargs,
        )
        
        ax[i].set_xlim(time[i].min(), time[i].max())
        if center_mean:
            ymean = np.mean(dat[i])
            yrange = np.max(np.abs(dat[i] - ymean))*1.2
            ax[i].set_ylim(ymean - yrange, ymean + yrange)
        else:
            ax[i].set_ylim(None,None)
        ax[i].set_ylim(np.array(ax[i].get_ylim()) / amp_factor)
        
        # ax[i].set_xlabel(xlabel)
        # ax[i].set_ylabel(ylabel)
        # ax[i].set_title(title)
        ax[i].tick_params(which ="both",direction = 'in')
        
        ax[i].xaxis.set_minor_locator(AutoMinorLocator(10))
        ax[i].yaxis.set_minor_locator(AutoMinorLocator(5))
        ax[i].yaxis.set_ticks_position('both')
        ax[i].xaxis.set_ticks_position('both')
        
        if chlabel is not None:
            ax[i].text(
                -0.1, 1,
                chlabel[i],
                va = "top",
                ha = "right",
                transform=ax[i].transAxes,
            )

        ax[i].grid()
    
    # fig.suptitle(title)
    ax[0].text(
        0.5, 1.1,
        title,
        va = "bottom",
        ha = "center",
        transform = ax[0].transAxes,
        )
    
    
    fig.tight_layout(
        # rect=[0, 0, 1, 0.96]
        )
    
    # ----------------------
    # Save figure
    # ----------------------
    if savefp is not None:
        savedir = os.path.dirname(savefp)
        if not os.path.exists(savedir):
            logger.info(f"Creating directory: {savedir}")
            os.makedirs(savedir)
            
        logger.info(f"Saving {savefp}")
        fig.savefig(savefp, bbox_inches="tight")
    return fig, ax