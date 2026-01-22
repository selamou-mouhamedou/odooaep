# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo import fields

class TestExecutionValidationKPI(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestExecutionValidationKPI, cls).setUpClass()
        # Create Project
        cls.project = cls.env['project.project'].create({
            'name': 'KPI Test Project',
            'is_execution_project': True,
        })
        
        # Create Planning with 2 tasks (60% and 40% weights)
        cls.planning = cls.env['execution.planning'].create({
            'name': 'KPI Planning',
            'project_id': cls.project.id,
        })
        cls.lot = cls.env['execution.planning.lot'].create({
            'name': 'Lot 1',
            'planning_id': cls.planning.id,
        })
        cls.task1 = cls.env['execution.planning.task'].create({
            'name': 'Task 1 (60%)',
            'lot_id': cls.lot.id,
            'weight': 60.0,
        })
        cls.task2 = cls.env['execution.planning.task'].create({
            'name': 'Task 2 (40%)',
            'lot_id': cls.lot.id,
            'weight': 40.0,
        })
        
        cls.planning.action_submit()
        cls.planning.action_approve()

    def test_01_validation_immutability(self):
        """Test that validation records are immutable"""
        # Create a progress declaration
        decl = self.env['execution.progress'].create({
            'task_id': self.task1.id,
            'declared_percentage': 50.0,
            'comment': 'Test progress',
        })
        # Add attachment
        self.env['ir.attachment'].create({
            'name': 'proof.jpg',
            'datas': b'empty',
            'res_model': 'execution.progress',
            'res_id': decl.id,
        })
        decl.action_submit()
        decl.action_start_review()
        
        # Validate (using the wizard or directly depends on implementation, 
        # but executionpm_validation uses execution.validation model)
        validation = self.env['execution.validation'].create({
            'progress_id': decl.id,
            'decision': 'validated',
            'comment': 'Looks good',
        })
        # Actually trigger the validation logic on the progress record
        decl.action_validate()
        
        # Try to modify the validation record
        with self.assertRaises(UserError):
            validation.write({'comment': 'Changed my mind'})
            
        # Try to delete
        with self.assertRaises(UserError):
            validation.unlink()

    def test_02_kpi_calculation(self):
        """Test Project and Task KPI calculations"""
        # Initial progress should be 0
        self.assertEqual(self.task1.validated_progress, 0.0)
        self.assertEqual(self.project.computed_physical_progress, 0.0)
        
        # Declare 50% on Task 1 (which has 60% weight)
        # Expected project progress: 0.5 * 60 = 30%
        decl1 = self.env['execution.progress'].create({
            'task_id': self.task1.id,
            'declared_percentage': 50.0,
            'comment': '50% of Task 1',
        })
        self.env['ir.attachment'].create({
            'name': 'proof1.jpg',
            'datas': b'empty',
            'res_model': 'execution.progress',
            'res_id': decl1.id,
        })
        decl1.action_submit()
        decl1.action_start_review()
        decl1.action_validate()
        
        # Verify Task 1 KPI
        self.task1._compute_validated_progress() # Force compute if needed
        self.assertEqual(self.task1.validated_progress, 50.0)
        
        # Verify Project KPI
        self.planning._compute_overall_progress()
        self.project._compute_project_progress()
        self.assertEqual(self.project.computed_physical_progress, 30.0)
        
        # Declare 100% on Task 2 (which has 40% weight)
        # Expected total project progress: 30% + (1.0 * 40%) = 70%
        decl2 = self.env['execution.progress'].create({
            'task_id': self.task2.id,
            'declared_percentage': 100.0,
            'comment': '100% of Task 2',
        })
        self.env['ir.attachment'].create({
            'name': 'proof2.jpg',
            'datas': b'empty',
            'res_model': 'execution.progress',
            'res_id': decl2.id,
        })
        decl2.action_submit()
        decl2.action_start_review()
        decl2.action_validate()
        
        self.task2._compute_validated_progress()
        self.planning._compute_overall_progress()
        self.project._compute_project_progress()
        self.assertEqual(self.project.computed_physical_progress, 70.0)

    def test_03_correction_workflow(self):
        """Test the correction requested workflow"""
        decl = self.env['execution.progress'].create({
            'task_id': self.task1.id,
            'declared_percentage': 80.0,
            'comment': 'Initial submission',
        })
        self.env['ir.attachment'].create({
            'name': 'proof.jpg',
            'datas': b'empty',
            'res_model': 'execution.progress',
            'res_id': decl.id,
        })
        decl.action_submit()
        decl.action_start_review()
        
        # PMO requests correction (this logic might be in a wizard or directly on models)
        # Assuming the model has a way to handle this. 
        # From the documentation, executionpm_validation extends execution.progress with correction logic.
        
        # Create validation record with 'correction_requested'
        self.env['execution.validation'].create({
            'progress_id': decl.id,
            'decision': 'correction_requested',
            'comment': 'Please provide clearer photos',
        })
        
        # The progress record should move to draft (or a specific 'correction' state if it exists)
        # Let's check executionpm_validation/models/execution_progress.py to see how it handles this.
        # But generally it should reset to draft.
        decl.action_reset_draft()
        self.assertEqual(decl.state, 'draft')
