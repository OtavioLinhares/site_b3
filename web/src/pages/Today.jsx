import React from 'react';
import SelicAnalysis from '../components/SelicAnalysis';
import WorldComparison from '../components/WorldComparison';
import B3Treemap from '../components/B3Treemap';
import Rankings from '../components/Rankings';

const Today = () => {
    return (
        <div className="page-today fade-in">
            <SelicAnalysis />
            <WorldComparison />
            <B3Treemap />
            <Rankings />
        </div>
    );
};

export default Today;
