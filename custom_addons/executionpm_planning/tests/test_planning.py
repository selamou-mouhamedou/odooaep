# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestExecutionPlanning(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestExecutionPlanning, cls).setUpClass()
        # Create a project
        cls.project = cls.env['project.project'].create({
            'name': 'Test infrastructure Project',
            'is_execution_project': True,
        })
        
    def test_01_planning_weight_validation(self):
        """Test that planning cannot be submitted if weights != 100%"""
        planning = self.env['execution.planning'].create({
            'name': 'Test Planning',
            'project_id': self.project.id,
        })
        lot = self.env['execution.planning.lot'].create({
            'name': 'Lot 1',
            'planning_id': planning.id,
        })
        # Add task with 50% weight
        self.env['execution.planning.task'].create({
            'name': 'Task 1',
            'lot_id': lot.id,
            'weight': 50.0,
        })
        
        # Try to submit - should fail as total is 50%
        with self.assertRaises(ValidationError):
            planning.action_submit()
            
        # Add another task with 50% weight
        self.env['execution.planning.task'].create({
            'name': 'Task 2',
            'lot_id': lot.id,
            'weight': 50.0,
        })
        
        # Now total is 100%, should succeed
        planning.action_submit()
        self.assertEqual(planning.state, 'submitted')

    def test_02_planning_workflow(self):
        """Test the full planning workflow: Draft -> Submitted -> Approved"""
        planning = self.env['execution.planning'].create({
            'name': 'Workflow Planning',
            'project_id': self.project.id,
        })
        lot = self.env['execution.planning.lot'].create({
            'name': 'Lot 1',
            'planning_id': planning.id,
        })
        self.env['execution.planning.task'].create({
            'name': 'Complete Task',
            'lot_id': lot.id,
            'weight': 100.0,
        })
        
        # Submit
        planning.action_submit()
        self.assertEqual(planning.state, 'submitted')
        
        # Approve
        planning.action_approve()
        self.assertEqual(planning.state, 'approved')
        self.assertEqual(planning.approved_by, self.env.user)
        self.assertTrue(planning.approved_date)
